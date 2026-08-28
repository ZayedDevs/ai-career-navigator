"""
CV Profile Extractor — extracts structured personal info from resume text.

Scope (intentionally limited):
    ✅ name, email, phone, linkedin, github, location — reliable regex extraction
    ✅ skills — passed in from skill_extractor (already working perfectly)
    ❌ education, experience, projects, certifications — NOT extracted
       (PDF text structure is too inconsistent; user fills these manually)
"""

import re
from datetime import datetime, timezone


# ============================================================================
# REGEX PATTERNS
# ============================================================================

EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

PHONE_PATTERN = re.compile(
    r"(?:\+?60|0)[\s\-]?1[0-9][\s\-]?\d{7,8}"   # Malaysian: +601x, 01x
    r"|(?:\+?\d{1,3}[\s\-]?)?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{4}"
)

LINKEDIN_PATTERN = re.compile(
    r"(?:linkedin\.com/in/)[\w\-\./]+"
)

GITHUB_PATTERN = re.compile(
    r"(?:github\.com/)[\w\-]+"
)

LOCATION_KEYWORDS = [
    "malaysia", "melaka", "kuala lumpur", "kl", "selangor", "penang",
    "johor", "sabah", "sarawak",
]


# ============================================================================
# HELPERS
# ============================================================================

def _clean(text: str) -> str:
    return " ".join(text.split()).strip()


def _is_contact_line(line: str) -> bool:
    """Return True if line looks like contact info rather than a name."""
    signals = ["@", "http", "linkedin", "github", "+", "tel:", "phone"]
    return any(s in line.lower() for s in signals)


def _is_label_line(line: str) -> bool:
    """Return True if line is a section header or job title label."""
    label_patterns = [
        r"^(student|engineer|developer|analyst|specialist|manager|consultant)",
        r"^(summary|profile|objective|skills|education|experience|projects)",
        r"^(area of expertise|technical skills|work experience)",
    ]
    l = line.lower().strip()
    return any(re.match(p, l) for p in label_patterns)


# ============================================================================
# EXTRACTORS
# ============================================================================

def _extract_name(lines: list) -> str:
    """
    Extract name from the first few lines of the resume.
    Heuristic: first non-empty line that is NOT contact info, NOT a label,
    NOT all-caps with more than 4 words (that's a heading/title).
    """
    for line in lines[:8]:
        line = _clean(line)
        if not line:
            continue
        if _is_contact_line(line):
            continue
        if _is_label_line(line):
            continue
        words = line.split()
        if len(words) < 2 or len(words) > 6:
            continue
        # All-caps single words are likely labels ("ZAYED KHALED" is OK,
        # "ARTIFICIAL INTELLIGENCE STUDENT" is a title — too many words)
        if len(words) > 3 and line.isupper():
            continue
        # Looks like a name
        return line

    return ""


def _extract_email(text: str) -> str:
    match = EMAIL_PATTERN.search(text)
    return match.group().strip() if match else ""


def _extract_phone(text: str) -> str:
    match = PHONE_PATTERN.search(text)
    return _clean(match.group()) if match else ""


def _extract_linkedin(text: str) -> str:
    match = LINKEDIN_PATTERN.search(text)
    return match.group().strip() if match else ""


def _extract_github(text: str) -> str:
    match = GITHUB_PATTERN.search(text)
    return match.group().strip() if match else ""


def _extract_location(text: str) -> str:
    """Try to find a Malaysian city/state mentioned near contact info."""
    text_lower = text.lower()
    for keyword in LOCATION_KEYWORDS:
        if keyword in text_lower:
            # Grab the surrounding context (up to 30 chars)
            idx = text_lower.find(keyword)
            snippet = text[max(0, idx - 10): idx + len(keyword) + 10]
            return _clean(snippet)
    return ""


# ============================================================================
# PUBLIC API
# ============================================================================

def extract_cv_profile(resume_text: str, user_skills: list = None) -> dict:
    """
    Extract structured personal info from raw resume text.

    Args:
        resume_text:  Raw text from resume_parser.parse_resume()
        user_skills:  Already-extracted skills (from skill_extractor)
                      If None, skills field will be empty.

    Returns:
        {
            "personal": { name, email, phone, location, linkedin, github },
            "summary": "",
            "skills": [...sorted skills...],
            "expertise": [],
            "education": [],
            "experience": [],
            "projects": [],
            "certifications": [],
            "source": "uploaded_resume",
            "extracted_at": ISO timestamp
        }

    Note:
        education, experience, projects, certifications are intentionally
        returned as empty arrays. The user fills these in the CV Builder form.
        Attempting to parse them from raw PDF text is unreliable.
    """
    if not resume_text or len(resume_text.strip()) < 20:
        return {"error": "Resume text too short to extract profile."}

    lines = [l.strip() for l in resume_text.split("\n") if l.strip()]

    personal = {
        "name":     _extract_name(lines),
        "email":    _extract_email(resume_text),
        "phone":    _extract_phone(resume_text),
        "location": _extract_location(resume_text),
        "linkedin": _extract_linkedin(resume_text),
        "github":   _extract_github(resume_text),
        "title":    "",   # User fills in (e.g. "AI Engineer")
    }

    return {
        "personal":       personal,
        "summary":        "",       # User writes or AI generates
        "skills":         sorted(user_skills or []),
        "expertise":      [],       # High-level domain labels user adds
        "education":      [],       # User fills manually
        "experience":     [],       # User fills manually
        "projects":       [],       # User fills manually
        "certifications": [],       # User fills manually
        "source":         "uploaded_resume",
        "extracted_at":   datetime.now(timezone.utc).isoformat(),
    }