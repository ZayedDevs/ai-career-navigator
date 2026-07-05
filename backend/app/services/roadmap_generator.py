from datetime import datetime, timezone

from .skill_tier import classify_skill
from .youtube_fetcher import get_youtube_resources

"""
Purpose:
    Generate a personalized 3-phase learning roadmap based on:
      1. User's missing skills (from gap_analyzer)
      2. Skill tier classification (from skill_tier service)
      3. YouTube video recommendations (from youtube_fetcher service)
"""


# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_MAX_SKILLS = 8         # Total skills in the roadmap (across all phases)
DEFAULT_VIDEOS_PER_SKILL = 3   # YouTube videos per skill

# Tier ordering (for phase assignment)
TIER_TO_PHASE = {
    1: 1,  # Foundation skills → Phase 1
    2: 2,  # Intermediate skills → Phase 2
    3: 3,  # Advanced skills → Phase 3
}

# Phase metadata
PHASE_METADATA = {
    1: {
        "tier_name": "Foundation",
        "description": "Build the essential base skills you'll use everywhere.",
        "icon": "🌱",
    },
    2: {
        "tier_name": "Intermediate",
        "description": "Master the role-specific tools and frameworks.",
        "icon": "🚀",
    },
    3: {
        "tier_name": "Advanced",
        "description": "Develop specialized expertise that sets you apart.",
        "icon": "⭐",
    },
}


# ============================================================================
# CORE LOGIC — SKILL PRIORITIZATION
# ============================================================================

def _prioritize_skills(missing_skills: list, max_skills: int) -> list:
    """
    Pick top N skills to include in the roadmap.
    Priority = frequency (% of jobs requiring it).

    Args:
        missing_skills: List of {skill, frequency_pct, ...} dicts from gap analyzer
        max_skills:     Maximum number of skills in the roadmap

    Returns:
        Top N skills by frequency
    """
    if not missing_skills:
        return []

    # Sort by frequency descending (most demanded first)
    sorted_skills = sorted(
        missing_skills,
        key=lambda x: -x.get("frequency_pct", 0),
    )

    return sorted_skills[:max_skills]


# ============================================================================
# CORE LOGIC — ENRICH SKILLS WITH TIER + RESOURCES
# ============================================================================

def _enrich_skill(skill_data: dict, include_resources: bool = True) -> dict:
    """
    Enrich a missing skill with tier classification and YouTube resources.

    Args:
        skill_data:        Dict with at least {"skill": str, "frequency_pct": float}
        include_resources: If True, fetch YouTube videos (slower but richer)

    Returns:
        Enriched skill dict ready for the roadmap output
    """
    skill_name = skill_data["skill"]

    # Get tier classification
    tier_info = classify_skill(skill_name)

    enriched = {
        "skill": skill_name,
        "frequency_pct": skill_data.get("frequency_pct", 0),
        "job_count": skill_data.get("job_count", 0),
        "tier": tier_info["tier"],
        "tier_name": tier_info["tier_name"],
        "category": tier_info["category"],
        "estimated_weeks": tier_info["weeks"],
        "phase": TIER_TO_PHASE[tier_info["tier"]],
    }

    # Compute priority label based on frequency
    freq = enriched["frequency_pct"]
    if freq >= 40:
        enriched["priority"] = "critical"
    elif freq >= 25:
        enriched["priority"] = "high"
    elif freq >= 15:
        enriched["priority"] = "medium"
    else:
        enriched["priority"] = "low"

    # Optionally fetch YouTube resources (uses cache)
    if include_resources:
        try:
            videos = get_youtube_resources(skill_name)
            enriched["resources"] = videos
            enriched["resource_count"] = len(videos)
        except Exception as e:
            print(f"WARNING: Failed to fetch resources for '{skill_name}': {e}")
            enriched["resources"] = []
            enriched["resource_count"] = 0
    else:
        enriched["resources"] = []
        enriched["resource_count"] = 0

    return enriched


# ============================================================================
# CORE LOGIC — GROUP INTO PHASES
# ============================================================================

def _group_into_phases(enriched_skills: list) -> list:
    """
    Group enriched skills into 3 phases (Foundation/Intermediate/Advanced).
    Within each phase, skills are sorted by frequency (highest first).

    Returns:
        List of phase dicts, in order [Phase 1, Phase 2, Phase 3]
    """
    phases = {1: [], 2: [], 3: []}

    for skill in enriched_skills:
        phase_num = skill["phase"]
        phases[phase_num].append(skill)

    # Sort skills within each phase by frequency descending
    for phase_num in phases:
        phases[phase_num].sort(key=lambda x: -x["frequency_pct"])

    # Build final phase objects (only include phases that have skills)
    result = []
    for phase_num in [1, 2, 3]:
        skills_in_phase = phases[phase_num]
        if not skills_in_phase:
            continue

        duration_weeks = sum(s["estimated_weeks"] for s in skills_in_phase)
        meta = PHASE_METADATA[phase_num]

        result.append({
            "phase": phase_num,
            "tier": meta["tier_name"],
            "icon": meta["icon"],
            "description": meta["description"],
            "skill_count": len(skills_in_phase),
            "duration_weeks": duration_weeks,
            "skills": skills_in_phase,
        })

    return result


# ============================================================================
# PUBLIC API
# ============================================================================

def generate_roadmap(
    missing_skills: list,
    target_role: str,
    max_skills: int = DEFAULT_MAX_SKILLS,
    include_resources: bool = True,
) -> dict:
    """
    Generate a personalized 3-phase learning roadmap.

    Args:
        missing_skills:    List of skill dicts from gap_analyzer
                          (output of analyze_single_role's missing_critical_skills)
        target_role:       The role the user is targeting (e.g., "Data Scientist")
        max_skills:        Total skills across all phases (default 8)
        include_resources: Whether to fetch YouTube videos (default True)

    Returns:
        {
            "target_role": str,
            "total_weeks": int,
            "skill_count": int,
            "phases": [list of phase dicts],
            "generated_at": ISO timestamp
        }
    """
    if not missing_skills:
        return {
            "target_role": target_role,
            "total_weeks": 0,
            "skill_count": 0,
            "phases": [],
            "message": "No missing skills to plan for — you're already job ready!",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # 1. Pick top N skills by frequency
    top_skills = _prioritize_skills(missing_skills, max_skills)

    # 2. Enrich each with tier + resources
    enriched = [_enrich_skill(s, include_resources) for s in top_skills]

    # 3. Group into phases
    phases = _group_into_phases(enriched)

    # 4. Calculate total timeline
    total_weeks = sum(p["duration_weeks"] for p in phases)

    return {
        "target_role": target_role,
        "total_weeks": total_weeks,
        "total_months": round(total_weeks / 4.33, 1),  # avg weeks per month
        "skill_count": len(enriched),
        "phase_count": len(phases),
        "phases": phases,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================================
# STANDALONE TEST
# ============================================================================

if __name__ == "__main__":
    """
    Test runner: generate a roadmap for a sample target role.

    Usage:
        python -m app.services.roadmap_generator
    """
    print("\n" + "=" * 76)
    print("  ROADMAP GENERATOR — TEST")
    print("=" * 76)

    # Simulate output from gap_analyzer for Data Scientist
    sample_missing_skills = [
        {"skill": "sql",                "frequency_pct": 40.5, "job_count": 562},
        {"skill": "pytorch",            "frequency_pct": 29.5, "job_count": 410},
        {"skill": "statistics",         "frequency_pct": 25.1, "job_count": 349},
        {"skill": "aws",                "frequency_pct": 24.0, "job_count": 333},
        {"skill": "data visualization", "frequency_pct": 23.5, "job_count": 327},
        {"skill": "deep learning",      "frequency_pct": 22.2, "job_count": 309},
        {"skill": "spark",              "frequency_pct": 21.2, "job_count": 295},
        {"skill": "communication",      "frequency_pct": 20.3, "job_count": 282},
    ]

    target_role = "Data Scientist"

    print(f"\nGenerating roadmap for target role: {target_role}")
    print(f"Input: {len(sample_missing_skills)} missing skills")
    print(f"(This will fetch YouTube videos — may take ~10 seconds first run)")

    roadmap = generate_roadmap(
        missing_skills=sample_missing_skills,
        target_role=target_role,
        max_skills=8,
        include_resources=True,
    )

    # Display
    print(f"\n{'=' * 76}")
    print(f"  🎯 LEARNING ROADMAP: {roadmap['target_role']}")
    print(f"{'=' * 76}")
    print(f"  Total duration:  {roadmap['total_weeks']} weeks ({roadmap['total_months']} months)")
    print(f"  Total skills:    {roadmap['skill_count']}")
    print(f"  Learning phases: {roadmap['phase_count']}")

    for phase in roadmap["phases"]:
        print(f"\n{'─' * 76}")
        print(f"  {phase['icon']}  PHASE {phase['phase']}: {phase['tier']}")
        print(f"     {phase['description']}")
        print(f"     Duration: {phase['duration_weeks']} weeks  |  {phase['skill_count']} skills")
        print(f"{'─' * 76}")

        for skill in phase["skills"]:
            priority_marker = {
                "critical": "🔴",
                "high":     "🟠",
                "medium":   "🟡",
                "low":      "🟢",
            }.get(skill["priority"], "⚪")

            print(f"\n    {priority_marker} {skill['skill'].upper()}")
            print(f"       Priority:     {skill['priority']}  ({skill['frequency_pct']}% of jobs)")
            print(f"       Category:     {skill['category']}")
            print(f"       Time to learn: {skill['estimated_weeks']} weeks")

            if skill["resources"]:
                print(f"       Top resources:")
                for i, res in enumerate(skill["resources"][:2], 1):
                    title = res['title'][:55]
                    print(f"          {i}. {title}")
                    print(f"             — {res['channel']}")
            else:
                print(f"       Resources: (none available)")

    print(f"\n{'=' * 76}")