"""Auth API routes: register, login, get current user."""

from flask import Blueprint, request, current_app
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity
)

from ..models.user_model import (
    create_user, authenticate_user, get_user_by_id
)
from ..utils.response_helper import success_response, error_response


auth_bp = Blueprint("auth", __name__)


# ============================================================================
# POST /api/auth/register
# ============================================================================

@auth_bp.route("/register", methods=["POST"])
def register():
    """Create a new account and return a JWT token."""
    try:
        if not request.is_json:
            return error_response("Content-Type must be application/json", 400)

        payload = request.get_json()
        if not payload:
            return error_response("Request body is empty.", 400)

        email = payload.get("email", "")
        password = payload.get("password", "")
        name = payload.get("name", "")

        if not email or not password:
            return error_response("Email and password are required.", 400)

        # Create user (raises ValueError on bad input)
        try:
            user = create_user(email=email, password=password, name=name)
        except ValueError as ve:
            return error_response(str(ve), 400)

        if user is None:
            return error_response(
                "An account with this email already exists.", 409
            )

        # Generate JWT token (identity = user id)
        token = create_access_token(identity=user["id"])

        return success_response(
            data={"token": token, "user": user},
            message="Account created successfully.",
            status_code=201,
        )

    except Exception as e:
        current_app.logger.exception("Registration failed")
        return error_response(f"An unexpected error occurred: {str(e)}", 500)


# ============================================================================
# POST /api/auth/login
# ============================================================================

@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate and return a JWT token."""
    try:
        if not request.is_json:
            return error_response("Content-Type must be application/json", 400)

        payload = request.get_json()
        if not payload:
            return error_response("Request body is empty.", 400)

        email = payload.get("email", "")
        password = payload.get("password", "")

        if not email or not password:
            return error_response("Email and password are required.", 400)

        user = authenticate_user(email, password)

        if user is None:
            return error_response("Invalid email or password.", 401)

        token = create_access_token(identity=user["id"])

        return success_response(
            data={"token": token, "user": user},
            message="Login successful.",
            status_code=200,
        )

    except Exception as e:
        current_app.logger.exception("Login failed")
        return error_response(f"An unexpected error occurred: {str(e)}", 500)


# ============================================================================
# GET /api/auth/me  (protected)
# ============================================================================

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """Return the currently authenticated user's data."""
    try:
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)

        if user is None:
            return error_response("User not found.", 404)

        return success_response(
            data={"user": user},
            message="Current user retrieved.",
        )

    except Exception as e:
        current_app.logger.exception("Get current user failed")
        return error_response(f"An unexpected error occurred: {str(e)}", 500)