import os
import json
import joblib
from functools import lru_cache

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

"""
Purpose:
    Compare a user's extracted skills against IT role categories using:
      - Cosine similarity (match percentage)
      - KNN-based readiness scoring (industry alignment)
      - Set-difference logic (missing skill identification)
      - Frequency-based prioritization (most demanded skills first)
"""


# ============================================================================
# CONFIGURATION
# ============================================================================

SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(SERVICE_DIR, "..", ".."))

MODELS_DIR = os.path.join(BACKEND_ROOT, "ml", "saved_models")
DATA_DIR = os.path.join(BACKEND_ROOT, "data", "processed")

TFIDF_PATH = os.path.join(MODELS_DIR, "tfidf_vectorizer.pkl")
KNN_PATH = os.path.join(MODELS_DIR, "knn_readiness_model.pkl")
SKILL_CORPUS_PATH = os.path.join(DATA_DIR, "skill_corpus.json")

TOP_N = 5                       # Number of top roles to return
MAX_MISSING_SKILLS = 15         # Missing skills shown per role (deep dive)
MAX_MISSING_OVERVIEW = 5        # Missing skills shown per role (overview/top 5)
TOP_SKILLS_PER_ROLE = 30        # How many top role skills to use as reference


# ============================================================================
# LAZY-LOADED RESOURCES
# ============================================================================

@lru_cache(maxsize=1)
def get_tfidf_vectorizer():
    """Load the trained TF-IDF vectorizer."""
    if not os.path.exists(TFIDF_PATH):
        raise FileNotFoundError(f"TF-IDF vectorizer not found at {TFIDF_PATH}")
    return joblib.load(TFIDF_PATH)


@lru_cache(maxsize=1)
def get_knn_model():
    """Load the KNN model (used for readiness scoring)."""
    if not os.path.exists(KNN_PATH):
        raise FileNotFoundError(f"KNN model not found at {KNN_PATH}")
    return joblib.load(KNN_PATH)


@lru_cache(maxsize=1)
def get_skill_corpus():
    """Load the role-to-skills mapping (built during preprocessing)."""
    if not os.path.exists(SKILL_CORPUS_PATH):
        raise FileNotFoundError(f"Skill corpus not found at {SKILL_CORPUS_PATH}")
    with open(SKILL_CORPUS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_available_roles() -> list:
    """Return list of all 12 role names from the corpus."""
    return sorted(get_skill_corpus().keys())


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def skills_to_text(skills_list: list) -> str:
    """Convert list of skills into comma-separated string (matches training format)."""
    return ", ".join(skills_list)


def vectorize_skills(skills_list: list):
    """Convert a skill list into a TF-IDF vector."""
    vectorizer = get_tfidf_vectorizer()
    text = skills_to_text(skills_list)
    return vectorizer.transform([text])


# ============================================================================
# CORE ANALYSIS — SINGLE ROLE COMPUTATION
# ============================================================================

def _compute_role_analysis(
    user_skills_set: set,
    user_vector,
    role_name: str,
    role_data: dict,
    vectorizer,
    max_missing: int = MAX_MISSING_OVERVIEW,
) -> dict:
    """
    Core computation engine — analyze user against ONE role.

    Shared by both top_5 and single_role endpoints.

    Returns:
        {
            "role":                       str,
            "match_percentage":           float (0-100),  // cosine similarity
            "matching_skills":            [list of skills user already has],
            "missing_critical_skills":    [list of {skill, frequency_pct, job_count}],
            "match_count":                int,
            "missing_count":              int,
            "role_top_skills_count":      int,
        }
    """
    role_top_skills = role_data["top_skills"][:TOP_SKILLS_PER_ROLE]
    role_skill_freq = role_data["skill_frequency"]
    role_job_count = role_data["job_count"]
    role_skills_set = set(role_top_skills)

    # 1. Skills user has that match this role's expectations
    matching = sorted(user_skills_set & role_skills_set)

    # 2. Skills user is missing — prioritized by industry demand frequency
    missing_set = role_skills_set - user_skills_set
    missing_list = []
    for skill in missing_set:
        freq_count = role_skill_freq.get(skill, 0)
        frequency_pct = round((freq_count / role_job_count) * 100, 1) if role_job_count else 0
        missing_list.append({
            "skill": skill,
            "frequency_pct": frequency_pct,
            "job_count": freq_count,
        })
    # Sort most-demanded first
    missing_list.sort(key=lambda x: -x["frequency_pct"])
    missing_critical = missing_list[:max_missing]

    # 3. Hybrid match score with weighted coverage
    # ─────────────────────────────────────────────────────────────────
    # Coverage isn't just "how many" — it's "which ones".
    # The TOP 10 most-demanded skills are weighted 3x more than rank 11-30.
    # Why? In real hiring, missing top 5 skills hurts you MUCH more than
    # missing skills ranked 25-30.
    # ─────────────────────────────────────────────────────────────────

    # Get the role's top 10 most-demanded skills (highest priority)
    top_10_skills = set(role_top_skills[:10])
    other_skills = set(role_top_skills[10:])  # ranks 11-30

    # Count matches in each tier
    matches_top_10 = len(user_skills_set & top_10_skills)
    matches_other = len(user_skills_set & other_skills)

    # Weighted score: top 10 worth 3x more
    weighted_score = (matches_top_10 * 3) + matches_other
    max_possible = (len(top_10_skills) * 3) + len(other_skills)
    coverage_score = weighted_score / max_possible if max_possible else 0

    # Component B — Cosine Similarity (semantic alignment)
    role_skills_text = ", ".join(role_top_skills)
    role_vector = vectorizer.transform([role_skills_text])
    cosine_score = float(cosine_similarity(user_vector, role_vector)[0][0])

    # Hybrid: 60% weighted coverage + 40% cosine
    hybrid_score = (0.6 * coverage_score) + (0.4 * cosine_score)
    match_percentage = round(hybrid_score * 100, 1)


    return {
        "role": role_name,
        "match_percentage": match_percentage,
        "matching_skills": matching,
        "missing_critical_skills": missing_critical,
        "match_count": len(matching),
        "missing_count": len(missing_set),
        "role_top_skills_count": len(role_top_skills),
    }


# ============================================================================
# CORE ANALYSIS — READINESS SCORE
# ============================================================================

def _compute_readiness_score(user_vector) -> float:
    """
    Compute overall career readiness using KNN nearest-neighbor similarity
    to real LinkedIn job postings.

    Methodology:
        1. Find the 5 most similar real job postings in our training data
        2. Compute average Euclidean distance to them
        3. Apply calibrated linear scaling

    Calibration rationale:
        Empirically, even well-aligned users have KNN distances around 1.0-1.1
        due to high-dimensional TF-IDF vector sparsity. We calibrate the scale
        so that:
            distance 0.7 (close to typical job)   → ~85% ready
            distance 1.0 (average professional)   → ~50% ready
            distance 1.3 (limited overlap)        → ~10% ready
            distance 1.4+ (very different)        → ~0%

    Returns:
        Readiness percentage (0-100)
    """
    knn = get_knn_model()
    distances, _ = knn.kneighbors(user_vector, n_neighbors=5)

    avg_distance = float(np.mean(distances))

    # Calibrated linear scaling
    # Maps distance range [0.5, 1.4] → readiness [100%, 0%]
    MIN_DIST = 0.5   # distance at which readiness = 100%
    MAX_DIST = 1.4   # distance at which readiness = 0%

    if avg_distance <= MIN_DIST:
        similarity = 1.0
    elif avg_distance >= MAX_DIST:
        similarity = 0.0
    else:
        # Linear interpolation between MIN and MAX
        similarity = 1.0 - ((avg_distance - MIN_DIST) / (MAX_DIST - MIN_DIST))

    return round(similarity * 100, 1)


# ============================================================================
# PUBLIC API — TOP 5 RECOMMENDATIONS (OVERVIEW MODE)
# ============================================================================

def analyze_top_5(user_skills: list) -> dict:
    """
    Compare user against ALL roles, return TOP 5 best matches.

    Used by:
        POST /api/gap/analyze  (no role specified)

    Args:
        user_skills: List of canonical skill strings.

    Returns:
        {
            "user_skills":                    [...],
            "user_skill_count":               int,
            "overall_readiness_percentage":   float,
            "top_5_matches":                  [list of 5 role analyses]
        }
    """
    if not user_skills or len(user_skills) == 0:
        return {
            "user_skills": [],
            "user_skill_count": 0,
            "overall_readiness_percentage": 0.0,
            "top_5_matches": [],
            "error": "No skills provided.",
        }

    vectorizer = get_tfidf_vectorizer()
    corpus = get_skill_corpus()

    user_vector = vectorize_skills(user_skills)
    user_skills_set = set(user_skills)

    # Analyze against each role
    analyses = []
    for role_name, role_data in corpus.items():
        analysis = _compute_role_analysis(
            user_skills_set=user_skills_set,
            user_vector=user_vector,
            role_name=role_name,
            role_data=role_data,
            vectorizer=vectorizer,
            max_missing=MAX_MISSING_OVERVIEW,
        )
        analyses.append(analysis)

    # Rank by match %
    analyses.sort(key=lambda x: -x["match_percentage"])
    top_matches = analyses[:TOP_N]
    for i, m in enumerate(top_matches, 1):
        m["rank"] = i

    readiness = _compute_readiness_score(user_vector)

    return {
        "user_skills": sorted(user_skills),
        "user_skill_count": len(user_skills),
        "overall_readiness_percentage": readiness,
        "top_5_matches": top_matches,
    }


# ============================================================================
# PUBLIC API — SINGLE ROLE DEEP DIVE
# ============================================================================

def analyze_single_role(user_skills: list, role_name: str) -> dict:
    """
    Deep gap analysis for ONE specific role.

    Used by:
        POST /api/gap/analyze/<role_name>

    Args:
        user_skills: List of canonical skill strings.
        role_name:   Exact role category name (e.g., "Data Scientist").

    Returns:
        {
            "user_skills":                  [...],
            "user_skill_count":             int,
            "target_role":                  str,
            "match_percentage":             float,
            "readiness_percentage":         float,
            "matching_skills":              [...],
            "missing_critical_skills":      [...],  // up to 15 skills, deeper
            "match_count":                  int,
            "missing_count":                int,
            "role_top_skills_count":        int,
        }
    """
    if not user_skills or len(user_skills) == 0:
        return {"error": "No skills provided."}

    corpus = get_skill_corpus()
    if role_name not in corpus:
        return {
            "error": f"Unknown role '{role_name}'. "
                     f"Available roles: {', '.join(sorted(corpus.keys()))}"
        }

    vectorizer = get_tfidf_vectorizer()
    user_vector = vectorize_skills(user_skills)
    user_skills_set = set(user_skills)

    analysis = _compute_role_analysis(
        user_skills_set=user_skills_set,
        user_vector=user_vector,
        role_name=role_name,
        role_data=corpus[role_name],
        vectorizer=vectorizer,
        max_missing=MAX_MISSING_SKILLS,
    )

    readiness = _compute_readiness_score(user_vector)

    return {
        "user_skills": sorted(user_skills),
        "user_skill_count": len(user_skills),
        "target_role": role_name,
        "match_percentage": analysis["match_percentage"],
        "readiness_percentage": readiness,
        "matching_skills": analysis["matching_skills"],
        "missing_critical_skills": analysis["missing_critical_skills"],
        "match_count": analysis["match_count"],
        "missing_count": analysis["missing_count"],
        "role_top_skills_count": analysis["role_top_skills_count"],
    }


# ============================================================================
# STANDALONE TEST RUNNER
# ============================================================================

if __name__ == "__main__":
    """
    Test runner — parse a resume, extract skills, and run gap analysis.

    Usage:
        python -m app.services.gap_analyzer <path_to_resume> [role_name]

    Examples:
        python -m app.services.gap_analyzer resume.pdf              # Top 5
        python -m app.services.gap_analyzer resume.pdf "Data Scientist"  # Deep dive
    """
    import sys
    from .resume_parser import parse_resume
    from .skill_extractor import extract_skills

    if len(sys.argv) < 2:
        print("Usage: python -m app.services.gap_analyzer <path_to_resume> [role_name]")
        sys.exit(1)

    file_path = sys.argv[1]
    target_role = sys.argv[2] if len(sys.argv) > 2 else None

    print("\n" + "=" * 78)
    print("  SKILL GAP ANALYZER — TEST")
    print("=" * 78)
    print(f"Resume: {file_path}")
    print(f"Mode:   {'DEEP DIVE → ' + target_role if target_role else 'TOP 5 RECOMMENDATIONS'}")

    # ── Stage 1: parse ──
    print("\n[1/3] Parsing resume...")
    parse_result = parse_resume(file_path)
    if not parse_result["success"]:
        print(f"✗ Parsing failed: {parse_result['error']}")
        sys.exit(1)
    print(f"✓ Parsed: {parse_result['word_count']} words")

    # ── Stage 2: extract ──
    print("\n[2/3] Extracting skills (first run loads spaCy ~10s)...")
    extract_result = extract_skills(parse_result["text"])
    print(f"✓ Extracted {extract_result['skill_count']} skills")

    # ── Stage 3: gap analysis ──
    if target_role:
        # ── DEEP-DIVE MODE ──
        print(f"\n[3/3] Running deep-dive gap analysis for '{target_role}'...")
        result = analyze_single_role(extract_result["skills"], target_role)

        if "error" in result:
            print(f"\n✗ Error: {result['error']}")
            sys.exit(1)

        print(f"\n{'=' * 78}")
        print(f"  📊 DEEP-DIVE: {result['target_role']}")
        print(f"{'=' * 78}")
        print(f"  Match score:           {result['match_percentage']}%")
        print(f"  Readiness score:       {result['readiness_percentage']}%")
        print(f"  Skills matched:        {result['match_count']} / {result['role_top_skills_count']}")
        print(f"  Skills missing:        {result['missing_count']}")

        if result["matching_skills"]:
            print(f"\n  ✅ Skills you already have ({len(result['matching_skills'])}):")
            for s in result["matching_skills"]:
                print(f"     ✓ {s}")

        if result["missing_critical_skills"]:
            print(f"\n  ⚠️  Top skills to learn (priority order):")
            for gap in result["missing_critical_skills"]:
                bar = "█" * int(gap["frequency_pct"] / 5)
                print(f"     • {gap['skill']:<25} {gap['frequency_pct']:>5.1f}% of jobs  {bar}")

    else:
        # ── TOP 5 MODE ──
        print("\n[3/3] Running top 5 recommendations...")
        result = analyze_top_5(extract_result["skills"])

        print(f"\n{'=' * 78}")
        print(f"  📊 OVERALL READINESS: {result['overall_readiness_percentage']}%")
        print(f"  📋 USER SKILLS:       {result['user_skill_count']}")
        print(f"{'=' * 78}")

        print(f"\n  🏆 TOP 5 CAREER MATCHES:")

        for match in result["top_5_matches"]:
            print(f"\n  {'─' * 76}")
            print(f"  #{match['rank']}: {match['role']}")
            print(f"  {'─' * 76}")
            print(f"     Match score:    {match['match_percentage']}%")
            print(f"     Skills matched: {match['match_count']} / {match['role_top_skills_count']}")
            print(f"     Skills missing: {match['missing_count']}")

            if match["matching_skills"]:
                # Show first 6 matching skills inline
                preview = ", ".join(match["matching_skills"][:6])
                if len(match["matching_skills"]) > 6:
                    preview += f", +{len(match['matching_skills']) - 6} more"
                print(f"     ✅ Have:         {preview}")

            if match["missing_critical_skills"]:
                print(f"     ⚠️  Top missing:")
                for gap in match["missing_critical_skills"][:5]:
                    bar = "█" * int(gap["frequency_pct"] / 5)
                    print(f"        • {gap['skill']:<22} {gap['frequency_pct']:>5.1f}%  {bar}")

    print("\n" + "=" * 78)