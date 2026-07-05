"""Dashboard data models: analyses, roadmaps, skill progress (per-user)."""

from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId

from ..utils.db import get_collection


ANALYSES_COLLECTION = "analyses"
ROADMAPS_COLLECTION = "roadmaps"
PROGRESS_COLLECTION = "skill_progress"


# ============================================================================
# HELPERS
# ============================================================================

def _to_oid(id_str: str):
    """Convert string to ObjectId, return None if invalid."""
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        return None


def _iso(dt):
    """Safely convert datetime to ISO string."""
    return dt.isoformat() if dt else None


# ============================================================================
# ANALYSES — Save resume analysis snapshots
# ============================================================================

def save_analysis(user_id: str, analysis_data: dict) -> dict | None:
    """
    Save a resume analysis snapshot for a user.

    analysis_data may contain:
        filename, extracted_skills, overall_readiness,
        top_matches, predicted_career, target_role
    """
    doc = {
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc),
        "filename": analysis_data.get("filename", "untitled"),
        "extracted_skills": analysis_data.get("extracted_skills", []),
        "skill_count": len(analysis_data.get("extracted_skills", [])),
        "overall_readiness": analysis_data.get("overall_readiness"),
        "top_matches": analysis_data.get("top_matches", []),
        "predicted_career": analysis_data.get("predicted_career"),
        "target_role": analysis_data.get("target_role"),
    }

    coll = get_collection(ANALYSES_COLLECTION)
    result = coll.insert_one(doc)
    doc["_id"] = result.inserted_id

    return _sanitize_analysis(doc)


def _sanitize_analysis(doc: dict) -> dict:
    """Convert analysis doc to API-safe dict."""
    if not doc:
        return None
    return {
        "id": str(doc["_id"]),
        "timestamp": _iso(doc.get("timestamp")),
        "filename": doc.get("filename"),
        "extracted_skills": doc.get("extracted_skills", []),
        "skill_count": doc.get("skill_count", 0),
        "overall_readiness": doc.get("overall_readiness"),
        "top_matches": doc.get("top_matches", []),
        "predicted_career": doc.get("predicted_career"),
        "target_role": doc.get("target_role"),
    }


def list_analyses(user_id: str, limit: int = 50) -> list:
    """Get all analyses for a user, newest first."""
    coll = get_collection(ANALYSES_COLLECTION)
    docs = coll.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
    return [_sanitize_analysis(d) for d in docs]


def get_analysis(user_id: str, analysis_id: str) -> dict | None:
    """Get a single analysis (only if it belongs to the user)."""
    oid = _to_oid(analysis_id)
    if not oid:
        return None
    coll = get_collection(ANALYSES_COLLECTION)
    doc = coll.find_one({"_id": oid, "user_id": user_id})
    return _sanitize_analysis(doc) if doc else None


def get_latest_analysis(user_id: str) -> dict | None:
    """Get the user's most recent analysis."""
    coll = get_collection(ANALYSES_COLLECTION)
    doc = coll.find_one({"user_id": user_id}, sort=[("timestamp", -1)])
    return _sanitize_analysis(doc) if doc else None


def delete_analysis(user_id: str, analysis_id: str) -> bool:
    """Delete an analysis (only if it belongs to the user)."""
    oid = _to_oid(analysis_id)
    if not oid:
        return False
    coll = get_collection(ANALYSES_COLLECTION)
    result = coll.delete_one({"_id": oid, "user_id": user_id})
    return result.deleted_count > 0


def count_analyses(user_id: str) -> int:
    """Count how many analyses a user has."""
    coll = get_collection(ANALYSES_COLLECTION)
    return coll.count_documents({"user_id": user_id})


# ============================================================================
# ROADMAPS — Save active learning roadmaps
# ============================================================================

def save_roadmap(user_id: str, roadmap_data: dict) -> dict | None:
    """
    Save a generated roadmap for a user.
    Replaces any existing roadmap for the same target_role.
    """
    target_role = roadmap_data.get("target_role", "Unknown")

    doc = {
        "user_id": user_id,
        "target_role": target_role,
        "total_weeks": roadmap_data.get("total_weeks", 0),
        "total_months": roadmap_data.get("total_months", 0),
        "phases": roadmap_data.get("phases", []),
        "skill_count": roadmap_data.get("skill_count", 0),
        "created_at": datetime.now(timezone.utc),
    }

    coll = get_collection(ROADMAPS_COLLECTION)
    # Upsert: one roadmap per (user, target_role)
    coll.replace_one(
        {"user_id": user_id, "target_role": target_role},
        doc,
        upsert=True,
    )

    saved = coll.find_one({"user_id": user_id, "target_role": target_role})
    return _sanitize_roadmap(saved)


def _sanitize_roadmap(doc: dict) -> dict:
    """Convert roadmap doc to API-safe dict."""
    if not doc:
        return None
    phases = doc.get("phases", [])
    return {
        "id": str(doc["_id"]),
        "target_role": doc.get("target_role"),
        "total_weeks": doc.get("total_weeks"),
        "total_months": doc.get("total_months"),
        "phases": phases,
        "phase_count": len(phases),
        "skill_count": doc.get("skill_count", 0),
        "created_at": _iso(doc.get("created_at")),
    }


def get_roadmap(user_id: str, roadmap_id: str) -> dict | None:
    """Get a single saved roadmap by ID (only if it belongs to the user)."""
    oid = _to_oid(roadmap_id)
    if not oid:
        return None
    coll = get_collection(ROADMAPS_COLLECTION)
    doc = coll.find_one({"_id": oid, "user_id": user_id})
    return _sanitize_roadmap(doc) if doc else None


def delete_roadmap(user_id: str, roadmap_id: str) -> bool:
    """Delete a roadmap (only if it belongs to the user)."""
    oid = _to_oid(roadmap_id)
    if not oid:
        return False
    coll = get_collection(ROADMAPS_COLLECTION)
    result = coll.delete_one({"_id": oid, "user_id": user_id})
    return result.deleted_count > 0


def list_roadmaps(user_id: str) -> list:
    """Get all roadmaps for a user, newest first."""
    coll = get_collection(ROADMAPS_COLLECTION)
    docs = coll.find({"user_id": user_id}).sort("created_at", -1)
    return [_sanitize_roadmap(d) for d in docs]


def get_active_roadmap(user_id: str) -> dict | None:
    """Get the user's most recent roadmap."""
    coll = get_collection(ROADMAPS_COLLECTION)
    doc = coll.find_one({"user_id": user_id}, sort=[("created_at", -1)])
    return _sanitize_roadmap(doc) if doc else None


# ============================================================================
# SKILL PROGRESS — Track learning/learned skills
# ============================================================================

def set_skill_progress(user_id: str, skill: str, status: str) -> dict | None:
    """
    Mark a skill as 'learning' or 'learned'.
    status must be one of: 'learning', 'learned'
    """
    skill_normalized = str(skill).strip().lower()
    if not skill_normalized:
        return None
    if status not in ("learning", "learned"):
        return None

    doc = {
        "user_id": user_id,
        "skill": skill_normalized,
        "status": status,
        "updated_at": datetime.now(timezone.utc),
    }

    coll = get_collection(PROGRESS_COLLECTION)
    coll.replace_one(
        {"user_id": user_id, "skill": skill_normalized},
        doc,
        upsert=True,
    )

    saved = coll.find_one({"user_id": user_id, "skill": skill_normalized})
    return _sanitize_progress(saved)


def _sanitize_progress(doc: dict) -> dict:
    """Convert progress doc to API-safe dict."""
    if not doc:
        return None
    return {
        "skill": doc.get("skill"),
        "status": doc.get("status"),
        "updated_at": _iso(doc.get("updated_at")),
    }


def list_progress(user_id: str) -> list:
    """Get all skill progress entries for a user."""
    coll = get_collection(PROGRESS_COLLECTION)
    docs = coll.find({"user_id": user_id}).sort("updated_at", -1)
    return [_sanitize_progress(d) for d in docs]


def remove_skill_progress(user_id: str, skill: str) -> bool:
    """Remove a skill from progress tracking."""
    skill_normalized = str(skill).strip().lower()
    coll = get_collection(PROGRESS_COLLECTION)
    result = coll.delete_one({"user_id": user_id, "skill": skill_normalized})
    return result.deleted_count > 0


def count_progress(user_id: str, status: str = None) -> int:
    """Count progress entries, optionally filtered by status."""
    coll = get_collection(PROGRESS_COLLECTION)
    query = {"user_id": user_id}
    if status:
        query["status"] = status
    return coll.count_documents(query)