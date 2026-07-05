from flask import Blueprint, request, current_app

from ..services.career_predictor import (
    predict_career,
    get_available_roles,
)
from ..utils.response_helper import success_response, error_response

"""
Purpose:
    HTTP endpoints for the Career Role Prediction module.
    Wraps career_predictor.py service with REST API conventions.
"""


# ============================================================================
# BLUEPRINT SETUP
# ============================================================================

prediction_bp = Blueprint("prediction", __name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_TOP_K = 3
MAX_ALLOWED_TOP_K = 11  # We have 11 role categories


# ============================================================================
# ENDPOINT: POST /api/predict/career
#   Predict best-fit career from user skills
# ============================================================================

@prediction_bp.route("/career", methods=["POST"])
def predict_user_career():
    """
    Predict the user's best-fit career role(s) from their skills.

    Request:
        Content-Type: application/json
        Body: {
            "skills": ["python", "machine learning", "sql", ...],
            "top_k": 3   // optional, default 3
        }

    Response (success):
        {
            "success": true,
            "message": "...",
            "data": {
                "user_skills": [...],
                "user_skill_count": int,
                "primary_prediction": {
                    "role":       "Data Scientist",
                    "confidence": 74.0
                },
                "top_predictions": [
                    {"role": "Data Scientist",   "confidence": 74.0},
                    {"role": "Software Engineer","confidence": 14.0},
                    {"role": "Data Analyst",     "confidence":  6.0}
                ],
                "career_readiness": {
                    "readiness_percentage": 65.4,
                    "avg_distance_to_real_jobs": 0.82
                },
                "all_role_confidences": [...]
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

        # ── 3. Validate optional top_k ──────────────────────────────────
        top_k = payload.get("top_k", DEFAULT_TOP_K)
        if not isinstance(top_k, int) or top_k < 1:
            top_k = DEFAULT_TOP_K
        if top_k > MAX_ALLOWED_TOP_K:
            top_k = MAX_ALLOWED_TOP_K

        # ── 4. Normalize skills ─────────────────────────────────────────
        normalized_skills = [
            str(s).strip().lower() for s in skills if str(s).strip()
        ]

        if len(normalized_skills) == 0:
            return error_response(
                "No valid skills found after normalization.",
                status_code=400,
            )

        # ── 5. Run prediction ───────────────────────────────────────────
        result = predict_career(normalized_skills, top_k=top_k)

        if "error" in result:
            return error_response(result["error"], status_code=400)

        # ── 6. Build success response ───────────────────────────────────
        primary = result["primary_prediction"]
        msg = (
            f"Predicted career: {primary['role']} "
            f"({primary['confidence']}% confidence)"
        )

        return success_response(
            data=result,
            message=msg,
            status_code=200,
        )

    except FileNotFoundError as e:
        current_app.logger.error(f"Missing required file: {e}")
        return error_response(
            "Server configuration error: required ML model missing. "
            "Run training scripts.",
            status_code=503,
        )

    except Exception as e:
        current_app.logger.exception("Career prediction failed")
        return error_response(
            f"An unexpected error occurred: {str(e)}",
            status_code=500,
        )


# ============================================================================
# ENDPOINT: GET /api/predict/roles
#   List the role classes the model can predict
# ============================================================================

@prediction_bp.route("/roles", methods=["GET"])
def list_predictable_roles():
    """
    Return the list of role categories the RF classifier can predict.
    """
    try:
        roles = get_available_roles()
        return success_response(
            data={"roles": roles, "count": len(roles)},
            message=f"{len(roles)} role classes available for prediction.",
        )

    except FileNotFoundError as e:
        current_app.logger.error(f"Missing required file: {e}")
        return error_response(
            "ML models not found. Run training first.",
            status_code=503,
        )

    except Exception as e:
        current_app.logger.exception("List roles failed")
        return error_response(f"An error occurred: {str(e)}", status_code=500)


# ============================================================================
# ENDPOINT: GET /api/predict/test
#   Health check for the prediction service
# ============================================================================

@prediction_bp.route("/test", methods=["GET"])
def test_prediction_service():
    """
    Verify the career predictor's ML models are loadable.
    """
    try:
        from ..services.career_predictor import (
            get_tfidf_vectorizer,
            get_rf_model,
            get_knn_model,
            get_label_encoder,
        )

        vectorizer = get_tfidf_vectorizer()
        rf = get_rf_model()
        knn = get_knn_model()
        encoder = get_label_encoder()

        return success_response(
            data={
                "service": "career_predictor",
                "status": "operational",
                "tfidf_vectorizer": {
                    "loaded": True,
                    "vocab_size": len(vectorizer.vocabulary_),
                },
                "random_forest": {
                    "loaded": True,
                    "n_estimators": rf.n_estimators,
                    "n_classes": rf.n_classes_,
                },
                "knn_readiness": {
                    "loaded": True,
                    "n_neighbors": knn.n_neighbors,
                },
                "label_encoder": {
                    "loaded": True,
                    "classes": sorted(encoder.classes_.tolist()),
                },
            },
            message="Career predictor service is operational.",
        )

    except Exception as e:
        return error_response(
            f"Career predictor service not operational: {str(e)}",
            status_code=500,
        )