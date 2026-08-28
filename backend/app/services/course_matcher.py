"""
Course Matcher Service — maps skills to Udemy/Coursera courses.
Loads the pre-built course_database.json and returns top matches per skill.
"""

import os
import json
from functools import lru_cache

# ============================================================================
# PATHS
# ============================================================================

SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(SERVICE_DIR, "..", ".."))
COURSE_DB_PATH = os.path.join(BACKEND_ROOT, "data", "courses", "course_database.json")


# ============================================================================
# LAZY-LOADED DATABASE
# ============================================================================

@lru_cache(maxsize=1)
def get_course_database() -> dict:
    """Load the course database (cached singleton)."""
    if not os.path.exists(COURSE_DB_PATH):
        raise FileNotFoundError(
            f"Course database not found at {COURSE_DB_PATH}. "
            f"Run ml/training/build_course_db.py first."
        )
    with open(COURSE_DB_PATH, encoding="utf-8") as f:
        return json.load(f)


# ============================================================================
# PUBLIC API
# ============================================================================

def get_courses_for_skill(
    skill: str,
    max_udemy: int = 2,
    max_coursera: int = 2,
) -> dict:
    """
    Get top Udemy and Coursera courses for a given skill.

    Args:
        skill:        Canonical skill name (e.g., "pytorch")
        max_udemy:    Max Udemy courses to return (default 2)
        max_coursera: Max Coursera courses to return (default 2)

    Returns:
        {
            "udemy":    [...up to 2 course dicts...],
            "coursera": [...up to 2 course dicts...],
        }
    """
    db = get_course_database()
    skills_index = db.get("skills", {})

    skill_lower = skill.lower().strip()

    # Direct match
    if skill_lower in skills_index:
        entry = skills_index[skill_lower]
        return {
            "udemy": entry.get("udemy", [])[:max_udemy],
            "coursera": entry.get("coursera", [])[:max_coursera],
        }

    # Fuzzy: check if skill is a substring of any indexed skill
    for indexed_skill, entry in skills_index.items():
        if skill_lower in indexed_skill or indexed_skill in skill_lower:
            return {
                "udemy": entry.get("udemy", [])[:max_udemy],
                "coursera": entry.get("coursera", [])[:max_coursera],
            }

    # No match — return empty (YouTube will still be shown)
    return {"udemy": [], "coursera": []}


def get_database_stats() -> dict:
    """Return metadata about the loaded course database."""
    try:
        db = get_course_database()
        return db.get("metadata", {})
    except FileNotFoundError:
        return {"error": "Course database not built yet"}