"""
CV Builder API routes.

Endpoints:
    GET    /api/cv/profile   → get saved CV profile
    POST   /api/cv/profile   → save / update CV profile
    POST   /api/cv/extract   → extract personal info from resume text
    PATCH  /api/cv/skills    → sync active_skills → CV profile skills
"""

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone
from bson import ObjectId

from ..services.cv_profile_extractor import extract_cv_profile
from ..utils.db import get_collection
from ..utils.response_helper import success_response, error_response

cv_bp = Blueprint("cv", __name__)

CV_COLLECTION = "cv_profiles"


# ============================================================================
# HELPERS
# ============================================================================

def _get_coll():
    return get_collection(CV_COLLECTION)


def _clean_profile(doc: dict) -> dict:
    """Strip MongoDB internals and return API-safe dict."""
    if not doc:
        return None
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    doc.pop("user_id", None)
    return doc


def _empty_profile() -> dict:
    """Return a blank profile structure for new users."""
    return {
        "personal": {
            "name":     "",
            "title":    "",
            "email":    "",
            "phone":    "",
            "location": "",
            "linkedin": "",
            "github":   "",
        },
        "summary":        "",
        "skills":         [],
        "expertise":      [],
        "education":      [],
        "experience":     [],
        "projects":       [],
        "certifications": [],
        "source":         "manual",
        "last_updated":   datetime.now(timezone.utc).isoformat(),
    }


# ============================================================================
# GET /api/cv/profile
# ============================================================================

@cv_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    """
    Get the user's saved CV profile.
    Returns null in data if no profile exists yet.
    """
    try:
        user_id = get_jwt_identity()
        doc = _get_coll().find_one({"user_id": user_id})

        if not doc:
            return success_response(
                data=None,
                message="No CV profile found.",
            )

        return success_response(
            data=_clean_profile(doc),
            message="CV profile retrieved.",
        )

    except Exception as e:
        current_app.logger.exception("GET /api/cv/profile failed")
        return error_response(str(e), 500)


# ============================================================================
# POST /api/cv/profile
# ============================================================================

@cv_bp.route("/profile", methods=["POST"])
@jwt_required()
def save_profile():
    """
    Save or update the user's CV profile.

    Body — all fields optional, existing values preserved for omitted fields:
    {
        "personal":       { name, title, email, phone, location, linkedin, github },
        "summary":        str,
        "skills":         [str, ...],
        "expertise":      [str, ...],
        "education":      [{ degree, institution, period, cgpa }, ...],
        "experience":     [{ title, company, period, bullets: [str] }, ...],
        "projects":       [{ name, period, role, bullets: [str] }, ...],
        "certifications": [str, ...]
    }
    """
    try:
        user_id = get_jwt_identity()

        if not request.is_json:
            return error_response("Content-Type must be application/json", 400)

        payload = request.get_json() or {}

        # Load existing or start from blank
        existing = _get_coll().find_one({"user_id": user_id}) or {}

        def _get(field, default):
            # Prefer incoming payload, fall back to existing, then default
            if field in payload:
                return payload[field]
            return existing.get(field, default)

        updated = {
            "user_id":        user_id,
            "personal":       _get("personal",       existing.get("personal", _empty_profile()["personal"])),
            "summary":        _get("summary",        existing.get("summary", "")),
            "skills":         sorted(set(_get("skills", existing.get("skills", [])))),
            "expertise":      _get("expertise",      existing.get("expertise", [])),
            "education":      _get("education",      existing.get("education", [])),
            "experience":     _get("experience",     existing.get("experience", [])),
            "projects":       _get("projects",       existing.get("projects", [])),
            "certifications": _get("certifications", existing.get("certifications", [])),
            "source":         payload.get("source",  existing.get("source", "manual")),
            "last_updated":   datetime.now(timezone.utc).isoformat(),
        }

        _get_coll().replace_one(
            {"user_id": user_id},
            updated,
            upsert=True,
        )

        saved = _get_coll().find_one({"user_id": user_id})
        return success_response(
            data=_clean_profile(saved),
            message="CV profile saved.",
        )

    except Exception as e:
        current_app.logger.exception("POST /api/cv/profile failed")
        return error_response(str(e), 500)


# ============================================================================
# POST /api/cv/extract
# ============================================================================

@cv_bp.route("/extract", methods=["POST"])
@jwt_required()
def extract_from_resume():
    """
    Extract personal info from raw resume text and save as CV profile.
    Called automatically after resume upload.

    Body:
    {
        "resume_text": "...",
        "skills": ["python", "java", ...]
    }

    Returns the saved profile with extracted personal info.
    Education, projects, experience start empty — user fills manually.
    """
    try:
        user_id = get_jwt_identity()

        if not request.is_json:
            return error_response("Content-Type must be application/json", 400)

        payload = request.get_json() or {}
        resume_text = payload.get("resume_text", "").strip()
        skills = payload.get("skills", [])

        if not resume_text:
            return error_response("'resume_text' is required.", 400)

        # Extract what we can reliably get
        extracted = extract_cv_profile(resume_text, skills)

        if "error" in extracted:
            return error_response(extracted["error"], 400)

        # Don't overwrite manually entered education/projects if they exist
        existing = _get_coll().find_one({"user_id": user_id}) or {}

        profile = {
            "user_id":        user_id,
            "personal":       extracted["personal"],
            "summary":        existing.get("summary", ""),
            "skills":         extracted["skills"],
            "expertise":      existing.get("expertise", []),
            "education":      existing.get("education", []),
            "experience":     existing.get("experience", []),
            "projects":       existing.get("projects", []),
            "certifications": existing.get("certifications", []),
            "source":         "uploaded_resume",
            "last_updated":   datetime.now(timezone.utc).isoformat(),
        }

        _get_coll().replace_one(
            {"user_id": user_id},
            profile,
            upsert=True,
        )

        saved = _get_coll().find_one({"user_id": user_id})
        return success_response(
            data=_clean_profile(saved),
            message="CV profile extracted from resume.",
            status_code=200,
        )

    except Exception as e:
        current_app.logger.exception("POST /api/cv/extract failed")
        return error_response(str(e), 500)


# ============================================================================
# PATCH /api/cv/skills
# ============================================================================

@cv_bp.route("/skills", methods=["PATCH"])
@jwt_required()
def sync_skills():
    """
    Merge the user's roadmap-learned skills into their CV profile.
    Called when the user opens the CV Builder page.

    Compares user.active_skills (from progress tracking) against
    cv_profile.skills and adds any that are missing.

    Returns:
    {
        "skills":        [...full merged list...],
        "new_additions": [...skills added this sync...]
    }
    """
    try:
        user_id = get_jwt_identity()

        # Get user's current active_skills (learned via roadmap)
        users_coll = get_collection("users")
        user = users_coll.find_one({"_id": ObjectId(user_id)})

        if not user:
            return error_response("User not found.", 404)

        active_skills = user.get("active_skills", [])

        # Get current CV profile skills
        coll = _get_coll()
        profile = coll.find_one({"user_id": user_id})

        if not profile:
            # No profile yet — just return the active_skills as-is
            return success_response(
                data={
                    "skills":        sorted(active_skills),
                    "new_additions": [],
                },
                message="No CV profile found. Upload a resume to get started.",
            )

        original_skills = profile.get("skills", [])
        merged_skills   = sorted(set(original_skills + active_skills))
        new_additions   = sorted(
            set(active_skills) - set(original_skills)
        )

        # Persist merged skills
        coll.update_one(
            {"user_id": user_id},
            {"$set": {
                "skills":       merged_skills,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }}
        )

        return success_response(
            data={
                "skills":        merged_skills,
                "new_additions": new_additions,
            },
            message=(
                f"{len(new_additions)} new skill(s) added from your roadmap."
                if new_additions
                else "Skills are already up to date."
            ),
        )

    except Exception as e:
        current_app.logger.exception("PATCH /api/cv/skills failed")
        return error_response(str(e), 500)