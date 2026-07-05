from flask import Blueprint, request, current_app

from ..services.roadmap_generator import generate_roadmap
from ..services.youtube_fetcher import get_cache_stats
from ..utils.response_helper import success_response, error_response

"""
Purpose:
    HTTP endpoint for the Roadmap Generator module.
"""

# ============================================================================
# BLUEPRINT SETUP
# ============================================================================

roadmap_bp = Blueprint("roadmap", __name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_MAX_SKILLS = 8
MAX_ALLOWED_SKILLS = 20    # Safety cap to prevent abuse


# ============================================================================
# ENDPOINT: POST /api/roadmap/generate
# ============================================================================

@roadmap_bp.route("/generate", methods=["POST"])
def generate_learning_roadmap():
    """
    Generate a personalized 3-phase learning roadmap.

    Request:
        Content-Type: application/json
        Body: {
            "target_role": "Data Scientist",
            "missing_skills": [
                {"skill": "sql", "frequency_pct": 40.5, "job_count": 562},
                {"skill": "pytorch", "frequency_pct": 29.5, "job_count": 410},
                ...
            ],
            "max_skills": 8,              // optional, default 8
            "include_resources": true     // optional, default true
        }

    Response (success):
        {
            "success": true,
            "message": "...",
            "data": {
                "target_role": "Data Scientist",
                "total_weeks": 25,
                "total_months": 5.8,
                "skill_count": 8,
                "phase_count": 3,
                "phases": [
                    {
                        "phase": 1,
                        "tier": "Foundation",
                        "icon": "🌱",
                        "description": "...",
                        "duration_weeks": 6,
                        "skill_count": 3,
                        "skills": [...]
                    },
                    ...
                ],
                "generated_at": "2026-..."
            }
        }
    """
    try:
        # ── 1. Validate request body ─────────────────────────────────────
        if not request.is_json:
            return error_response(
                "Content-Type must be application/json",
                status_code=400,
            )

        payload = request.get_json()

        if not payload:
            return error_response(
                "Request body is empty.",
                status_code=400,
            )

        # ── 2. Validate required fields ─────────────────────────────────
        if "target_role" not in payload:
            return error_response(
                "Missing required field: 'target_role'",
                status_code=400,
            )

        if "missing_skills" not in payload:
            return error_response(
                "Missing required field: 'missing_skills'",
                status_code=400,
            )

        target_role = str(payload["target_role"]).strip()
        missing_skills = payload["missing_skills"]

        # ── 3. Validate target_role ─────────────────────────────────────
        if not target_role:
            return error_response(
                "'target_role' cannot be empty.",
                status_code=400,
            )

        # ── 4. Validate missing_skills structure ────────────────────────
        if not isinstance(missing_skills, list):
            return error_response(
                "'missing_skills' must be a list of skill dictionaries.",
                status_code=400,
            )

        if len(missing_skills) == 0:
            return error_response(
                "'missing_skills' list is empty. Provide at least one skill.",
                status_code=400,
            )

        # Each skill must have at least {"skill": str, "frequency_pct": float}
        for i, s in enumerate(missing_skills):
            if not isinstance(s, dict):
                return error_response(
                    f"missing_skills[{i}] must be a dictionary.",
                    status_code=400,
                )
            if "skill" not in s:
                return error_response(
                    f"missing_skills[{i}] must contain 'skill' field.",
                    status_code=400,
                )

        # ── 5. Validate optional fields ─────────────────────────────────
        max_skills = payload.get("max_skills", DEFAULT_MAX_SKILLS)
        if not isinstance(max_skills, int) or max_skills < 1:
            max_skills = DEFAULT_MAX_SKILLS
        if max_skills > MAX_ALLOWED_SKILLS:
            max_skills = MAX_ALLOWED_SKILLS  # Cap for safety

        include_resources = payload.get("include_resources", True)
        if not isinstance(include_resources, bool):
            include_resources = True

        # ── 6. Generate the roadmap ─────────────────────────────────────
        roadmap = generate_roadmap(
            missing_skills=missing_skills,
            target_role=target_role,
            max_skills=max_skills,
            include_resources=include_resources,
        )

        # ── 7. Build success response ───────────────────────────────────
        msg = (
            f"Roadmap generated for '{target_role}': "
            f"{roadmap['skill_count']} skills across "
            f"{roadmap['phase_count']} phases over {roadmap['total_weeks']} weeks."
        )

        return success_response(
            data=roadmap,
            message=msg,
            status_code=200,
        )

    except FileNotFoundError as e:
        current_app.logger.error(f"Missing required file: {e}")
        return error_response(
            "Server configuration error: required ML artifact missing.",
            status_code=503,
        )

    except Exception as e:
        current_app.logger.exception("Roadmap generation failed")
        return error_response(
            f"An unexpected error occurred: {str(e)}",
            status_code=500,
        )


# ============================================================================
# ENDPOINT: GET /api/roadmap/test
# ============================================================================

@roadmap_bp.route("/test", methods=["GET"])
def test_roadmap_service():
    """
    Verify the roadmap generator dependencies are operational.
    """
    try:
        # Test skill tier classifier
        from ..services.skill_tier import classify_skill, get_tier_summary
        tier_summary = get_tier_summary()

        # Test YouTube fetcher (without making API call)
        from ..services.youtube_fetcher import YOUTUBE_API_KEY
        youtube_configured = bool(YOUTUBE_API_KEY)

        # Test cache
        cache_stats = get_cache_stats()

        return success_response(
            data={
                "service": "roadmap_generator",
                "status": "operational",
                "skill_tier_classifier": {
                    "loaded": True,
                    "curated_skills": tier_summary["total_curated"],
                    "foundation": tier_summary["foundation_count"],
                    "intermediate": tier_summary["intermediate_count"],
                    "advanced": tier_summary["advanced_count"],
                },
                "youtube_fetcher": {
                    "api_key_configured": youtube_configured,
                    "cache_stats": cache_stats,
                },
            },
            message="Roadmap service is operational.",
        )

    except Exception as e:
        return error_response(
            f"Roadmap service not operational: {str(e)}",
            status_code=500,
        )