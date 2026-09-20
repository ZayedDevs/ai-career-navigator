
import os
import uuid
from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from ..services.resume_parser import parse_resume
from ..services.skill_extractor import extract_skills
from ..services.cv_profile_extractor import extract_cv_profile
from ..utils.db import get_collection
from ..utils.response_helper import success_response, error_response

"""
Purpose:
    Handle HTTP requests for resume upload and skill extraction.
"""



# ============================================================================
# BLUEPRINT SETUP
# ============================================================================

# Blueprint allows us to group related routes. They get registered in __init__.py
resume_bp = Blueprint("resume", __name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    if "." not in filename:
        return False
    ext = "." + filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def get_upload_folder() -> str:
    """Get absolute path to the uploads folder, create if missing."""
    upload_folder = os.path.join(
        os.path.dirname(current_app.root_path),  # backend/
        "uploads",
    )
    os.makedirs(upload_folder, exist_ok=True)
    return upload_folder


# ============================================================================
# ENDPOINT: POST /api/resume/upload
# ============================================================================

@resume_bp.route("/upload", methods=["POST"])
@jwt_required(optional=True)
def upload_resume():
    """
    Upload a resume file (PDF or DOCX) and get extracted skills.

    Request:
        Content-Type: multipart/form-data
        Form field:   resume (file)

    Response (success):
        {
            "success": true,
            "message": "Skills extracted successfully",
            "data": {
                "filename": "original_name.pdf",
                "metadata": {...},
                "extracted_text_preview": "first 200 chars...",
                "skills": ["python", "java", ...],
                "skill_count": 23,
                "extraction_stats": {...}
            }
        }

    Response (error):
        {
            "success": false,
            "message": "Human-readable error",
            "data": null
        }
    """
    temp_path = None  # used for cleanup in finally block

    try:
        # ─── 1. Validate request contains file ───────────────────────────
        if "resume" not in request.files:
            return error_response(
                "No file provided. Send a multipart/form-data POST with field 'resume'.",
                status_code=400,
            )

        file = request.files["resume"]

        # Empty filename means user submitted form without selecting a file
        if file.filename == "":
            return error_response(
                "No file selected. Please choose a resume file.",
                status_code=400,
            )

        # ─── 2. Validate file extension ──────────────────────────────────
        if not is_allowed_file(file.filename):
            return error_response(
                f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
                status_code=400,
            )

        # ─── 3. Validate file size (read into memory first to check) ─────
        # Flask handles MAX_CONTENT_LENGTH globally too, but we double-check
        file.seek(0, os.SEEK_END)  # seek to end
        file_size = file.tell()    # get position = size
        file.seek(0)               # rewind to start

        if file_size == 0:
            return error_response("Uploaded file is empty.", status_code=400)

        if file_size > MAX_FILE_SIZE_BYTES:
            return error_response(
                f"File too large ({file_size / (1024*1024):.1f} MB). "
                f"Maximum is {MAX_FILE_SIZE_MB} MB.",
                status_code=413,  # Payload Too Large
            )

        # ─── 4. Save file with a safe unique name ────────────────────────
        # secure_filename() strips dangerous characters
        original_name = secure_filename(file.filename)
        ext = "." + original_name.rsplit(".", 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex}{ext}"

        upload_folder = get_upload_folder()
        temp_path = os.path.join(upload_folder, unique_name)
        file.save(temp_path)

        # ─── 5. Parse the resume ─────────────────────────────────────────
        parse_result = parse_resume(temp_path)

        if not parse_result["success"]:
            return error_response(
                parse_result["error"] or "Failed to parse resume.",
                status_code=400,
            )

        # ─── 6. Extract skills ───────────────────────────────────────────
        extract_result = extract_skills(parse_result["text"])

        # ─── 6b. Persist an autofill draft for the CV Builder (best-effort) ──
        # Non-fatal: a Mongo hiccup here must never break the upload response.
        user_id = get_jwt_identity()
        if user_id:
            try:
                extracted_profile = extract_cv_profile(
                    parse_result["text"], extract_result["skills"]
                )
                if "error" not in extracted_profile:
                    get_collection("resume_extracts").replace_one(
                        {"user_id": user_id},
                        {
                            "user_id":         user_id,
                            "personal":        extracted_profile["personal"],
                            "skills":          extracted_profile["skills"],
                            "source_filename": original_name,
                            "extracted_at":    extracted_profile["extracted_at"],
                        },
                        upsert=True,
                    )
            except Exception:
                current_app.logger.exception("Failed to persist resume_extracts draft")

        # ─── 7. Build successful response ────────────────────────────────
        data = {
            "filename": original_name,
            "metadata": parse_result["metadata"],
            "extracted_text_preview": parse_result["text"][:200],
            "char_count": parse_result["char_count"],
            "word_count": parse_result["word_count"],
            "skills": extract_result["skills"],
            "skill_count": extract_result["skill_count"],
            "extraction_stats": extract_result["extraction_details"],
        }

        return success_response(
            data=data,
            message=f"Extracted {extract_result['skill_count']} skills from '{original_name}'.",
            status_code=200,
        )

    except Exception as e:
        # Catch-all for unexpected errors — log and return generic message
        current_app.logger.exception("Resume upload failed")
        return error_response(
            f"An unexpected error occurred: {str(e)}",
            status_code=500,
        )

    finally:
        # ─── ALWAYS cleanup the temp file (privacy + disk space) ─────────
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as cleanup_err:
                current_app.logger.warning(
                    f"Failed to delete temp file {temp_path}: {cleanup_err}"
                )


# ============================================================================
# ENDPOINT: GET /api/resume/test
# ============================================================================

@resume_bp.route("/test", methods=["GET"])
def test_resume_service():
    """
    Health check for the resume service.
    Confirms all required models/files are loadable.
    """
    try:
        from ..services.skill_extractor import (
            get_skill_database,
            get_tfidf_vectorizer,
            get_spacy_model,
        )

        skill_db = get_skill_database()
        tfidf = get_tfidf_vectorizer()
        # spaCy: only load if not too slow — skip to keep this fast
        # nlp = get_spacy_model()  # uncomment if you want full check

        return success_response(
            data={
                "service": "resume",
                "status": "operational",
                "skill_database": {
                    "loaded": True,
                    "skill_count": skill_db["skill_count"],
                },
                "tfidf_vectorizer": {
                    "loaded": True,
                    "vocab_size": len(tfidf.vocabulary_),
                },
                "spacy": {"loaded": "deferred (loads on first extraction)"},
            },
            message="Resume service is operational.",
        )

    except Exception as e:
        return error_response(
            f"Resume service is not operational: {str(e)}",
            status_code=500,
        )