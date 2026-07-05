"""AI Tutor chat routes — powered by OpenAI."""

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..models.user_model import get_user_by_id
from ..models.dashboard_model import get_latest_analysis, get_active_roadmap, list_progress
from ..utils.response_helper import success_response, error_response

chat_bp = Blueprint("chat", __name__)


# ──────────────────────────────────────────────────────────────────────────────
# System prompt builder
# ──────────────────────────────────────────────────────────────────────────────

def _build_system_prompt(user: dict, latest_analysis, active_roadmap, progress: list) -> str:
    name        = user.get("name", "the user")
    target_role = (
        user.get("target_role")
        or (latest_analysis or {}).get("target_role")
        or "not yet set"
    )

    skills   = (latest_analysis or {}).get("extracted_skills", [])
    learned  = [p["skill"] for p in progress if p.get("status") == "learned"]
    learning = [p["skill"] for p in progress if p.get("status") == "learning"]

    roadmap_line = ""
    if active_roadmap:
        roadmap_line = (
            f"\nActive roadmap: {active_roadmap['target_role']} "
            f"({active_roadmap.get('skill_count', 0)} skills, "
            f"{active_roadmap.get('total_weeks', 0)} weeks)"
        )

    return f"""You are an expert AI career tutor for "AI Career Navigator", a platform that helps tech professionals level up their careers.

User profile:
- Name: {name}
- Target role: {target_role}
- Current skills ({len(skills)}): {', '.join(skills[:25]) if skills else 'not uploaded yet'}
- Skills learned: {', '.join(learned) if learned else 'none yet'}
- Skills in progress: {', '.join(learning) if learning else 'none'}{roadmap_line}

Guidelines:
- Be conversational, encouraging, and concise (under 300 words unless detail is needed)
- Refer to the user's actual skills and progress when relevant
- Give concrete, actionable advice — not vague platitudes
- When suggesting resources, prefer free/widely available ones
- Respond in plain prose — no markdown headers or bullet-heavy walls of text
- If asked about career paths, tailor advice to their skill set above"""


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────

@chat_bp.route("/message", methods=["POST"])
@jwt_required()
def send_message():
    """
    Send a chat message to the AI tutor.

    Body:
        {
            "message": "What roadmap should I pick?",
            "history": [
                {"role": "user",      "content": "..."},
                {"role": "assistant", "content": "..."}
            ]
        }

    Returns:
        { "reply": "..." }
    """
    # ── guard: openai installed? ──────────────────────────────────────────────
    try:
        import openai
    except ImportError:
        return error_response(
            "OpenAI package not installed on the server. "
            "Run: pip install openai",
            503,
        )

    # ── guard: API key configured? ────────────────────────────────────────────
    api_key = current_app.config.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return error_response(
            "OpenAI API key not configured. "
            "Add OPENAI_API_KEY=sk-... to your backend .env file.",
            503,
        )

    try:
        user_id = get_jwt_identity()
        payload = request.get_json(silent=True) or {}

        message = (payload.get("message") or "").strip()
        if not message:
            return error_response("'message' is required.", 400)

        history = payload.get("history") or []

        # ── build context ─────────────────────────────────────────────────────
        user            = get_user_by_id(user_id) or {}
        latest_analysis = get_latest_analysis(user_id)
        active_roadmap  = get_active_roadmap(user_id)
        progress        = list_progress(user_id)

        system_prompt = _build_system_prompt(
            user, latest_analysis, active_roadmap, progress
        )

        # ── assemble messages ─────────────────────────────────────────────────
        messages = [{"role": "system", "content": system_prompt}]

        # keep last 20 messages (10 exchanges) for context window efficiency
        for msg in history[-20:]:
            if msg.get("role") in ("user", "assistant") and msg.get("content"):
                messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": message})

        # ── call OpenAI ───────────────────────────────────────────────────────
        model  = current_app.config.get("OPENAI_MODEL", "gpt-3.5-turbo")
        client = openai.OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=600,
            temperature=0.7,
        )

        reply = response.choices[0].message.content.strip()
        return success_response(data={"reply": reply}, message="Response generated.")

    except openai.AuthenticationError:
        return error_response("Invalid OpenAI API key — check your .env file.", 401)
    except openai.RateLimitError:
        return error_response("OpenAI rate limit reached. Please try again in a moment.", 429)
    except openai.APIConnectionError:
        return error_response("Could not reach OpenAI. Check your internet connection.", 503)
    except Exception as e:
        current_app.logger.exception("Chat failed")
        return error_response(f"An error occurred: {str(e)}", 500)
