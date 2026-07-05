import re
import bcrypt
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId

from ..utils.db import get_collection

"""
Purpose:
    User data model + CRUD operations on MongoDB 'users' collection.
    Handles password hashing/verification using bcrypt.
"""

# ============================================================================
# CONSTANTS
# ============================================================================

USERS_COLLECTION = "users"
EMAIL_REGEX = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")
MIN_PASSWORD_LENGTH = 6
MAX_PASSWORD_LENGTH = 128


# ============================================================================
# COLLECTION ACCESSOR
# ============================================================================

def get_users_collection():
    """Get the MongoDB users collection (with email index)."""
    coll = get_collection(USERS_COLLECTION)
    # Ensure unique index on email (idempotent — only creates if missing)
    try:
        coll.create_index("email", unique=True)
    except Exception:
        pass  # Already exists
    return coll


# ============================================================================
# PASSWORD UTILITIES
# ============================================================================

def hash_password(password: str) -> bytes:
    """Hash a password using bcrypt (cost factor 12 — secure default)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))


def verify_password(password: str, password_hash: bytes) -> bool:
    """Verify a password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash)
    except Exception:
        return False


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def is_valid_email(email: str) -> bool:
    """Check if email format is valid."""
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def is_valid_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength.

    Returns:
        (is_valid, error_message)
    """
    if not password or not isinstance(password, str):
        return False, "Password is required."
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    if len(password) > MAX_PASSWORD_LENGTH:
        return False, f"Password must be at most {MAX_PASSWORD_LENGTH} characters."
    return True, ""


# ============================================================================
# SANITIZER — Convert MongoDB doc to API-safe dict
# ============================================================================

def _sanitize_user(user_doc: dict) -> dict:
    """Convert MongoDB user doc to a clean dict (removes password_hash, fixes _id)."""
    if not user_doc:
        return None
    return {
        "id": str(user_doc["_id"]),
        "email": user_doc["email"],
        "name": user_doc.get("name", ""),
        "target_role": user_doc.get("target_role"),
        "active_skills": user_doc.get("active_skills", []),
        "created_at": user_doc.get("created_at").isoformat() if user_doc.get("created_at") else None,
        "last_login_at": user_doc.get("last_login_at").isoformat() if user_doc.get("last_login_at") else None,
    }


# ============================================================================
# CRUD — CREATE
# ============================================================================

def create_user(email: str, password: str, name: str = "") -> dict | None:
    """
    Create a new user.

    Returns:
        Sanitized user dict if created, None if email already exists.

    Raises:
        ValueError if validation fails.
    """
    # Validate
    if not is_valid_email(email):
        raise ValueError("Invalid email format.")

    valid_pw, pw_error = is_valid_password(password)
    if not valid_pw:
        raise ValueError(pw_error)

    email_normalized = email.strip().lower()
    name_clean = (name or "").strip()[:100]

    # Build document
    now = datetime.now(timezone.utc)
    user_doc = {
        "email": email_normalized,
        "password_hash": hash_password(password),
        "name": name_clean,
        "target_role": None,
        "active_skills": [],
        "created_at": now,
        "last_login_at": None,
    }

    # Insert
    try:
        collection = get_users_collection()
        result = collection.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        return _sanitize_user(user_doc)
    except Exception as e:
        # Duplicate key error → email already exists
        if "duplicate" in str(e).lower() or "E11000" in str(e):
            return None
        raise


# ============================================================================
# CRUD — READ
# ============================================================================

def get_user_by_id(user_id: str) -> dict | None:
    """Get a user by their ObjectId. Returns sanitized dict (no password)."""
    try:
        oid = ObjectId(user_id)
    except (InvalidId, TypeError):
        return None

    collection = get_users_collection()
    user_doc = collection.find_one({"_id": oid})
    return _sanitize_user(user_doc) if user_doc else None


def get_user_by_email(email: str) -> dict | None:
    """Get a user by email. Returns sanitized dict (no password)."""
    if not email:
        return None
    collection = get_users_collection()
    user_doc = collection.find_one({"email": email.strip().lower()})
    return _sanitize_user(user_doc) if user_doc else None


# ============================================================================
# AUTHENTICATION
# ============================================================================

def authenticate_user(email: str, password: str) -> dict | None:
    """
    Verify email + password and return user data if valid.

    Returns:
        Sanitized user dict if successful, None if credentials invalid.
    """
    if not email or not password:
        return None

    collection = get_users_collection()
    user_doc = collection.find_one({"email": email.strip().lower()})

    if not user_doc:
        return None  # User not found

    if not verify_password(password, user_doc["password_hash"]):
        return None  # Wrong password

    # Update last_login_at
    collection.update_one(
        {"_id": user_doc["_id"]},
        {"$set": {"last_login_at": datetime.now(timezone.utc)}},
    )

    return _sanitize_user(user_doc)


# ============================================================================
# CRUD — UPDATE
# ============================================================================

def update_user_skills(user_id: str, skills: list) -> bool:
    """
    Update the user's active_skills (this is the evolving skill set).
    Used when user marks a skill as 'learned' — it gets added permanently.
    """
    try:
        oid = ObjectId(user_id)
    except (InvalidId, TypeError):
        return False

    # Normalize: lowercase, deduplicate
    normalized = sorted({str(s).strip().lower() for s in skills if str(s).strip()})

    collection = get_users_collection()
    result = collection.update_one(
        {"_id": oid},
        {"$set": {"active_skills": normalized}},
    )
    return result.matched_count > 0


def add_user_skill(user_id: str, skill: str) -> bool:
    """Add a single skill to user's active_skills (if not already there)."""
    try:
        oid = ObjectId(user_id)
    except (InvalidId, TypeError):
        return False

    skill_normalized = str(skill).strip().lower()
    if not skill_normalized:
        return False

    collection = get_users_collection()
    result = collection.update_one(
        {"_id": oid},
        {"$addToSet": {"active_skills": skill_normalized}},
    )
    return result.matched_count > 0


def remove_user_skill(user_id: str, skill: str) -> bool:
    """Remove a single skill from user's active_skills."""
    try:
        oid = ObjectId(user_id)
    except (InvalidId, TypeError):
        return False

    skill_normalized = str(skill).strip().lower()
    if not skill_normalized:
        return False

    collection = get_users_collection()
    result = collection.update_one(
        {"_id": oid},
        {"$pull": {"active_skills": skill_normalized}},
    )
    return result.matched_count > 0


def update_user_profile(user_id: str, updates: dict) -> bool:
    """
    Update profile fields. Only allows safe fields:
      - name
      - target_role
    """
    try:
        oid = ObjectId(user_id)
    except (InvalidId, TypeError):
        return False

    SAFE_FIELDS = {"name", "target_role"}
    safe_updates = {k: v for k, v in updates.items() if k in SAFE_FIELDS}

    if not safe_updates:
        return False

    collection = get_users_collection()
    result = collection.update_one({"_id": oid}, {"$set": safe_updates})
    return result.matched_count > 0