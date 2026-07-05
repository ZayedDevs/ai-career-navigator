"""
================================================================================
AI Career Navigator — Skill Gap API Routes
================================================================================
Author: Zayed Khaled Habeb Alkhulaqi (B032310764)

Purpose:
    HTTP endpoints for the Skill Gap Analysis module.
    Wraps gap_analyzer.py service with REST API conventions.

Endpoints:
    POST /api/gap/analyze              → Top 5 role recommendations
    POST /api/gap/analyze/<role_name>  → Deep-dive for one role
    GET  /api/gap/roles                → List available roles
    GET  /api/gap/test                 → Service health check

Used by:
    React frontend (Phase 9)
    Postman / curl for testing
================================================================================
"""

from flask import Blueprint, request, current_app
from urllib.parse import unquote

from ..services.gap_analyzer import (
    analyze_top_5,
    analyze_single_role,
    get_available_roles,
)
from ..utils.response_helper import success_response, error_response


# ============================================================================
# BLUEPRINT SETUP
# ============================================================================

gap_bp = Blueprint("gap", __name__)


# ============================================================================
# ENDPOINT: POST /api/gap/analyze
#   Top 5 role recommendations based on user skills
# ============================================================================

@gap_bp.route("/analyze", methods=["POST"])
def analyze_skills_top_5():
    """
    Analyze user's skills and return TOP 5 best-matching career roles.

    Request:
        Content-Type: application/json
        Body: {
            "skills": ["python", "java", "react", "mongodb", ...]
        }

    Response (success):
        {
            "success": true,
            "message": "...",
            "data": {
                "user_skills": [...],
                "user_skill_count": int,
                "overall_readiness_percentage": float,
                "top_5_matches": [
                    {
                        "rank": 1,
                        "role": "Data Scientist",
                        "match_percentage": 24.0,
                        "matching_skills": [...],
                        "missing_critical_skills": [
                            {"skill": "sql", "frequency_pct": 40.5, "job_count": 563},
                            ...
                        ],
                        ...
                    },
                    ... (4 more)
                ]
            }
        }

    Response (error):
        { "success": false, "message": "...", "data": null }
    """
    try:
        # ── 1. Validate request body ─────────────────────────────────────
        if not request.is_json:
            return error_response(
                "Content-Type must be application/json",
                status_code=400,
            )

        payload = request.get_json()

        if not payload or "skills" not in payload:
            return error_response(
                "Request body must contain a 'skills' field (list of strings).",
                status_code=400,
            )

        skills = payload["skills"]

        # ── 2. Validate skills format ───────────────────────────────────
        if not isinstance(skills, list):
            return error_response(
                "'skills' must be a list of skill strings.",
                status_code=400,
            )

        if len(skills) == 0:
            return error_response(
                "'skills' list is empty. Provide at least one skill.",
                status_code=400,
            )

        # Normalize: strip, lowercase, drop empties
        normalized_skills = [
            str(s).strip().lower() for s in skills if str(s).strip()
        ]

        if len(normalized_skills) == 0:
            return error_response(
                "No valid skills found after normalization.",
                status_code=400,
            )

        # ── 3. Run gap analysis ─────────────────────────────────────────
        result = analyze_top_5(normalized_skills)

        # ── 4. Build success response ───────────────────────────────────
        return success_response(
            data=result,
            message=f"Top {len(result['top_5_matches'])} career matches identified.",
            status_code=200,
        )

    except FileNotFoundError as e:
        # Models or corpus not found
        current_app.logger.error(f"Missing required file: {e}")
        return error_response(
            f"Server configuration error: required ML artifact missing. "
            f"Please run preprocessing and training scripts.",
            status_code=503,  # Service Unavailable
        )

    except Exception as e:
        current_app.logger.exception("Top 5 gap analysis failed")
        return error_response(
            f"An unexpected error occurred: {str(e)}",
            status_code=500,
        )


# ============================================================================
# ENDPOINT: POST /api/gap/analyze/<role_name>
#   Deep-dive analysis for ONE specific role
# ============================================================================

@gap_bp.route("/analyze/<path:role_name>", methods=["POST"])
def analyze_skills_single_role(role_name: str):
    """
    Deep gap analysis for ONE specific role.

    URL Parameter:
        role_name: Role category name (URL-encoded if it has spaces)
                   Example: "Data Scientist" or "Data%20Scientist"

    Request:
        Content-Type: application/json
        Body: { "skills": ["python", "ml", ...] }

    Response (success):
        {
            "success": true,
            "data": {
                "user_skills": [...],
                "target_role": "Data Scientist",
                "match_percentage": 23.5,
                "readiness_percentage": 38.7,
                "matching_skills": [...],
                "missing_critical_skills": [...],  # Up to 15 skills
                "match_count": 6,
                "missing_count": 24,
                "role_top_skills_count": 30
            }
        }
    """
    try:
        # ── 1. Decode URL-encoded role name (e.g., "Data%20Scientist") ──
        role_name_decoded = unquote(role_name)

        # ── 2. Validate role exists ─────────────────────────────────────
        available = get_available_roles()
        if role_name_decoded not in available:
            return error_response(
                f"Unknown role '{role_name_decoded}'. "
                f"Available roles: {', '.join(available)}",
                status_code=404,
            )

        # ── 3. Validate request body ────────────────────────────────────
        if not request.is_json:
            return error_response(
                "Content-Type must be application/json",
                status_code=400,
            )

        payload = request.get_json()
        if not payload or "skills" not in payload:
            return error_response(
                "Request body must contain a 'skills' field.",
                status_code=400,
            )

        skills = payload["skills"]
        if not isinstance(skills, list) or len(skills) == 0:
            return error_response(
                "'skills' must be a non-empty list of strings.",
                status_code=400,
            )

        # ── 4. Normalize skills ─────────────────────────────────────────
        normalized_skills = [
            str(s).strip().lower() for s in skills if str(s).strip()
        ]
        if len(normalized_skills) == 0:
            return error_response(
                "No valid skills found after normalization.",
                status_code=400,
            )

        # ── 5. Run deep-dive analysis ───────────────────────────────────
        result = analyze_single_role(normalized_skills, role_name_decoded)

        if "error" in result:
            return error_response(result["error"], status_code=400)

        # ── 6. Build success response ───────────────────────────────────
        return success_response(
            data=result,
            message=f"Deep-dive analysis for '{role_name_decoded}' complete.",
            status_code=200,
        )

    except FileNotFoundError as e:
        current_app.logger.error(f"Missing required file: {e}")
        return error_response(
            f"Server configuration error: required ML artifact missing.",
            status_code=503,
        )

    except Exception as e:
        current_app.logger.exception("Single-role gap analysis failed")
        return error_response(
            f"An unexpected error occurred: {str(e)}",
            status_code=500,
        )


# ============================================================================
# ENDPOINT: GET /api/gap/roles
#   List all available role categories
# ============================================================================

@gap_bp.route("/roles", methods=["GET"])
def list_roles():
    """
    Return the list of all available role categories.
    Useful for the frontend to populate dropdown menus.

    Response:
        {
            "success": true,
            "data": {
                "roles": ["Backend Developer", "Cybersecurity Analyst", ...],
                "count": 11
            }
        }
    """
    try:
        roles = get_available_roles()
        return success_response(
            data={"roles": roles, "count": len(roles)},
            message=f"{len(roles)} roles available.",
        )

    except FileNotFoundError as e:
        current_app.logger.error(f"Missing required file: {e}")
        return error_response(
            "Skill corpus not found. Run preprocessing first.",
            status_code=503,
        )

    except Exception as e:
        current_app.logger.exception("List roles failed")
        return error_response(f"An error occurred: {str(e)}", status_code=500)


# ============================================================================
# ENDPOINT: GET /api/gap/test
#   Health check for the gap service
# ============================================================================

@gap_bp.route("/test", methods=["GET"])
def test_gap_service():
    """
    Verify the gap analyzer's ML models and data are loadable.
    """
    try:
        from ..services.gap_analyzer import (
            get_tfidf_vectorizer,
            get_knn_model,
            get_skill_corpus,
        )

        vectorizer = get_tfidf_vectorizer()
        knn = get_knn_model()
        corpus = get_skill_corpus()

        return success_response(
            data={
                "service": "gap_analyzer",
                "status": "operational",
                "tfidf_vectorizer": {
                    "loaded": True,
                    "vocab_size": len(vectorizer.vocabulary_),
                },
                "knn_model": {
                    "loaded": True,
                    "n_neighbors": knn.n_neighbors,
                },
                "skill_corpus": {
                    "loaded": True,
                    "roles": len(corpus),
                    "role_names": sorted(corpus.keys()),
                },
            },
            message="Gap analyzer service is operational.",
        )

    except Exception as e:
        return error_response(
            f"Gap service not operational: {str(e)}",
            status_code=500,
        )