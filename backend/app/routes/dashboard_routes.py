"""Dashboard API routes: analyses, roadmaps, progress, stats (all protected)."""

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..models.dashboard_model import (
    save_analysis, list_analyses, get_analysis,
    get_latest_analysis, delete_analysis, count_analyses,
    save_roadmap, list_roadmaps, get_roadmap, get_active_roadmap, delete_roadmap,
    set_skill_progress, list_progress, remove_skill_progress,
    count_progress,
)
from ..models.user_model import get_user_by_id, add_user_skill, remove_user_skill, update_user_skills
from ..utils.response_helper import success_response, error_response


dashboard_bp = Blueprint("dashboard", __name__)


# ============================================================================
# ANALYSES
# ============================================================================

@dashboard_bp.route("/analyses", methods=["POST"])
@jwt_required()
def create_analysis():
    """Save a resume analysis snapshot."""
    try:
        user_id = get_jwt_identity()
        payload = request.get_json()
        if not payload:
            return error_response("Request body is empty.", 400)

        saved = save_analysis(user_id, payload)
        return success_response(
            data=saved,
            message="Analysis saved.",
            status_code=201,
        )
    except Exception as e:
        current_app.logger.exception("Save analysis failed")
        return error_response(f"An error occurred: {str(e)}", 500)


@dashboard_bp.route("/analyses", methods=["GET"])
@jwt_required()
def get_analyses():
    """List all of the user's analyses."""
    try:
        user_id = get_jwt_identity()
        analyses = list_analyses(user_id)
        return success_response(
            data={"analyses": analyses, "count": len(analyses)},
            message=f"{len(analyses)} analyses found.",
        )
    except Exception as e:
        current_app.logger.exception("List analyses failed")
        return error_response(f"An error occurred: {str(e)}", 500)


@dashboard_bp.route("/analyses/latest", methods=["GET"])
@jwt_required()
def get_latest():
    """Get the user's most recent analysis."""
    try:
        user_id = get_jwt_identity()
        latest = get_latest_analysis(user_id)
        if not latest:
            return success_response(
                data=None,
                message="No analyses yet.",
            )
        return success_response(data=latest, message="Latest analysis retrieved.")
    except Exception as e:
        current_app.logger.exception("Get latest failed")
        return error_response(f"An error occurred: {str(e)}", 500)


@dashboard_bp.route("/analyses/<analysis_id>", methods=["GET"])
@jwt_required()
def get_one_analysis(analysis_id):
    """Get a specific analysis by ID."""
    try:
        user_id = get_jwt_identity()
        analysis = get_analysis(user_id, analysis_id)
        if not analysis:
            return error_response("Analysis not found.", 404)
        return success_response(data=analysis, message="Analysis retrieved.")
    except Exception as e:
        current_app.logger.exception("Get analysis failed")
        return error_response(f"An error occurred: {str(e)}", 500)


@dashboard_bp.route("/analyses/<analysis_id>", methods=["DELETE"])
@jwt_required()
def remove_analysis(analysis_id):
    """Delete a specific analysis."""
    try:
        user_id = get_jwt_identity()
        deleted = delete_analysis(user_id, analysis_id)
        if not deleted:
            return error_response("Analysis not found.", 404)
        return success_response(data=None, message="Analysis deleted.")
    except Exception as e:
        current_app.logger.exception("Delete analysis failed")
        return error_response(f"An error occurred: {str(e)}", 500)


# ============================================================================
# ROADMAPS
# ============================================================================

@dashboard_bp.route("/roadmaps", methods=["POST"])
@jwt_required()
def create_roadmap():
    """Save a roadmap for the user."""
    try:
        user_id = get_jwt_identity()
        payload = request.get_json()
        if not payload:
            return error_response("Request body is empty.", 400)

        saved = save_roadmap(user_id, payload)
        return success_response(
            data=saved,
            message="Roadmap saved.",
            status_code=201,
        )
    except Exception as e:
        current_app.logger.exception("Save roadmap failed")
        return error_response(f"An error occurred: {str(e)}", 500)


@dashboard_bp.route("/roadmaps", methods=["GET"])
@jwt_required()
def get_roadmaps():
    """List all of the user's roadmaps."""
    try:
        user_id = get_jwt_identity()
        roadmaps = list_roadmaps(user_id)
        return success_response(
            data={"roadmaps": roadmaps, "count": len(roadmaps)},
            message=f"{len(roadmaps)} roadmaps found.",
        )
    except Exception as e:
        current_app.logger.exception("List roadmaps failed")
        return error_response(f"An error occurred: {str(e)}", 500)


@dashboard_bp.route("/roadmaps/<roadmap_id>", methods=["DELETE"])
@jwt_required()
def remove_roadmap(roadmap_id):
    """Delete a saved roadmap by ID."""
    try:
        user_id = get_jwt_identity()
        deleted = delete_roadmap(user_id, roadmap_id)
        if not deleted:
            return error_response("Roadmap not found.", 404)
        return success_response(data=None, message="Roadmap deleted.")
    except Exception as e:
        current_app.logger.exception("Delete roadmap failed")
        return error_response(f"An error occurred: {str(e)}", 500)


@dashboard_bp.route("/roadmaps/<roadmap_id>", methods=["GET"])
@jwt_required()
def get_one_roadmap(roadmap_id):
    """Get a single saved roadmap by ID."""
    try:
        user_id = get_jwt_identity()
        roadmap = get_roadmap(user_id, roadmap_id)
        if not roadmap:
            return error_response("Roadmap not found.", 404)
        return success_response(data=roadmap, message="Roadmap retrieved.")
    except Exception as e:
        current_app.logger.exception("Get roadmap failed")
        return error_response(f"An error occurred: {str(e)}", 500)


@dashboard_bp.route("/roadmaps/active", methods=["GET"])
@jwt_required()
def get_active():
    """Get the user's active (most recent) roadmap."""
    try:
        user_id = get_jwt_identity()
        active = get_active_roadmap(user_id)
        if not active:
            return success_response(data=None, message="No active roadmap.")
        return success_response(data=active, message="Active roadmap retrieved.")
    except Exception as e:
        current_app.logger.exception("Get active roadmap failed")
        return error_response(f"An error occurred: {str(e)}", 500)


# ============================================================================
# SKILL PROGRESS (with skill evolution — Option Y)
# ============================================================================

@dashboard_bp.route("/progress", methods=["POST"])
@jwt_required()
def mark_progress():
    """
    Mark a skill as 'learning' or 'learned'.

    Body: { "skill": "sql", "status": "learned" }

    When status is 'learned', the skill is ALSO added to the user's
    active_skills (Option Y — skill evolution).
    """
    try:
        user_id = get_jwt_identity()
        payload = request.get_json()
        if not payload:
            return error_response("Request body is empty.", 400)

        skill = payload.get("skill", "")
        status = payload.get("status", "")

        if not skill:
            return error_response("'skill' is required.", 400)
        if status not in ("learning", "learned"):
            return error_response(
                "'status' must be 'learning' or 'learned'.", 400
            )

        result = set_skill_progress(user_id, skill, status)
        if not result:
            return error_response("Failed to update progress.", 400)

        # Option Y: if learned, evolve the user's active skill set
        skill_added_to_profile = False
        if status == "learned":
            skill_added_to_profile = add_user_skill(user_id, skill)

        return success_response(
            data={
                "progress": result,
                "added_to_active_skills": skill_added_to_profile,
            },
            message=f"Skill '{skill}' marked as {status}.",
        )
    except Exception as e:
        current_app.logger.exception("Mark progress failed")
        return error_response(f"An error occurred: {str(e)}", 500)


@dashboard_bp.route("/progress", methods=["GET"])
@jwt_required()
def get_progress():
    """List all of the user's skill progress."""
    try:
        user_id = get_jwt_identity()
        progress = list_progress(user_id)
        return success_response(
            data={"progress": progress, "count": len(progress)},
            message=f"{len(progress)} progress entries found.",
        )
    except Exception as e:
        current_app.logger.exception("List progress failed")
        return error_response(f"An error occurred: {str(e)}", 500)


@dashboard_bp.route("/progress/<skill>", methods=["DELETE"])
@jwt_required()
def delete_progress(skill):
    """Remove a skill from progress tracking."""
    try:
        user_id = get_jwt_identity()
        removed = remove_skill_progress(user_id, skill)
        if not removed:
            return error_response("Skill not found in progress.", 404)
        remove_user_skill(user_id, skill)  # keep active_skills in sync
        return success_response(data=None, message=f"'{skill}' removed from progress.")
    except Exception as e:
        current_app.logger.exception("Delete progress failed")
        return error_response(f"An error occurred: {str(e)}", 500)


# ============================================================================
# ACTIVE SKILLS (user profile skill list)
# ============================================================================

@dashboard_bp.route("/active-skills/<skill>", methods=["DELETE"])
@jwt_required()
def delete_active_skill(skill):
    """Remove a single skill from the user's active_skills."""
    try:
        user_id = get_jwt_identity()
        removed = remove_user_skill(user_id, skill)
        if not removed:
            return error_response("Skill not found in active skills.", 404)
        return success_response(data=None, message=f"'{skill}' removed from active skills.")
    except Exception as e:
        current_app.logger.exception("Delete active skill failed")
        return error_response(f"An error occurred: {str(e)}", 500)


@dashboard_bp.route("/active-skills", methods=["DELETE"])
@jwt_required()
def clear_active_skills():
    """Clear all active skills from the user's profile."""
    try:
        user_id = get_jwt_identity()
        update_user_skills(user_id, [])
        return success_response(data=None, message="All active skills cleared.")
    except Exception as e:
        current_app.logger.exception("Clear active skills failed")
        return error_response(f"An error occurred: {str(e)}", 500)


# ============================================================================
# DASHBOARD STATS (overview for the dashboard landing page)
# ============================================================================

@dashboard_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_stats():
    """
    Aggregate dashboard stats for the overview page.
    """
    try:
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        if not user:
            return error_response("User not found.", 404)

        latest = get_latest_analysis(user_id)
        active_roadmap = get_active_roadmap(user_id)

        total_analyses = count_analyses(user_id)
        skills_learned = count_progress(user_id, "learned")
        skills_learning = count_progress(user_id, "learning")

        # Roadmap completion (if there's an active roadmap)
        roadmap_progress = None
        if active_roadmap:
            total_roadmap_skills = active_roadmap.get("skill_count", 0)
            if total_roadmap_skills > 0:
                roadmap_progress = {
                    "target_role": active_roadmap["target_role"],
                    "total_skills": total_roadmap_skills,
                    "skills_completed": skills_learned,
                    "percent_complete": round(
                        (skills_learned / total_roadmap_skills) * 100, 1
                    ) if total_roadmap_skills else 0,
                }

        return success_response(
            data={
                "user": {
                    "name": user["name"],
                    "email": user["email"],
                    "target_role": user.get("target_role"),
                    "active_skill_count": len(user.get("active_skills", [])),
                },
                "total_analyses": total_analyses,
                "skills_learned": skills_learned,
                "skills_learning": skills_learning,
                "latest_analysis": latest,
                "active_roadmap": active_roadmap,
                "roadmap_progress": roadmap_progress,
            },
            message="Dashboard stats retrieved.",
        )
    except Exception as e:
        current_app.logger.exception("Get stats failed")
        return error_response(f"An error occurred: {str(e)}", 500)