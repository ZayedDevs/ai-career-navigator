"""
Build a skill → course lookup database from Udemy and Coursera datasets.
Outputs: backend/data/courses/course_database.json
"""

import os
import re
import json
import pandas as pd

# ============================================================================
# PATHS
# ============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
COURSES_DIR = os.path.join(BACKEND_ROOT, "data", "courses")

UDEMY_CSV = os.path.join(COURSES_DIR, "udemy_courses_raw.csv")
COURSERA_CSV = os.path.join(COURSES_DIR, "coursera_courses_raw.csv")
OUTPUT_JSON = os.path.join(COURSES_DIR, "course_database.json")


# ============================================================================
# CONFIGURATION
# ============================================================================

# Udemy categories relevant to IT
IT_CATEGORIES = {
    "Development",
    "IT & Software",
    "Data Science",
    "Cloud Computing",
    "Network & Security",
    "Office Productivity",  # covers Excel, SQL tools
}

# Skills we want to match (must match your skill_database.pkl canonical names)
TARGET_SKILLS = [
    # Languages
    "python", "java", "javascript", "typescript", "c++", "c#",
    "rust", "kotlin", "swift", "php", "ruby", "scala",
    "bash", "powershell",

    # Web
    "html", "css", "react", "angular", "vue", "node.js",
    "next.js", "tailwind", "bootstrap",

    # Backend
    "flask", "django", "fastapi", "spring boot", "express",
    "rest api", "graphql",

    # Databases
    "sql", "mysql", "postgresql", "mongodb", "redis",
    "sqlite", "oracle database", "sql server", "firebase",

    # ML/AI
    "machine learning", "deep learning", "tensorflow", "pytorch",
    "scikit-learn", "pandas", "numpy", "computer vision",
    "natural language processing", "nlp", "data analysis",
    "data visualization", "statistics", "tableau", "power bi",

    # Cloud
    "aws", "azure", "gcp", "docker", "kubernetes",
    "terraform", "ansible", "ci/cd",

    # Data Engineering
    "spark", "hadoop", "kafka", "airflow", "snowflake", "databricks",

    # Security
    "cybersecurity", "penetration testing", "owasp", "cissp",
    "network security", "ethical hacking",

    # Networking
    "networking", "ccna", "linux",

    # Soft skills / methodology
    "agile", "scrum", "git", "devops",
]


# ============================================================================
# HELPERS
# ============================================================================

def slugify(title: str) -> str:
    """Convert course title to Coursera URL slug."""
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = slug.strip("-")
    return slug


def parse_rating(rating_str) -> float:
    """Parse Coursera rating like '4.8(20K reviews)' → 4.8"""
    if pd.isna(rating_str):
        return 0.0
    match = re.search(r"[\d.]+", str(rating_str))
    return float(match.group()) if match else 0.0


def parse_difficulty(metadata_str: str) -> str:
    """Parse 'Beginner · Professional Certificate · 3 - 6 Months' → 'Beginner'"""
    if pd.isna(metadata_str):
        return "All Levels"
    parts = str(metadata_str).split("·")
    return parts[0].strip() if parts else "All Levels"


def normalize(text: str) -> str:
    """Lowercase and strip."""
    return str(text).lower().strip()


def text_contains_skill(text: str, skill: str) -> bool:
    """Check if text contains a skill using word-boundary matching."""
    if not text or not skill:
        return False
    escaped = re.escape(skill.lower())
    pattern = rf"(?<![a-zA-Z0-9]){escaped}(?![a-zA-Z0-9])"
    return bool(re.search(pattern, text.lower()))


# ============================================================================
# UDEMY PROCESSING
# ============================================================================

def process_udemy(path: str) -> list:
    """Load, filter, and clean Udemy dataset."""
    print(f"\n[UDEMY] Loading {os.path.basename(path)}...")
    df = pd.read_csv(path, low_memory=False)
    print(f"  Raw: {len(df):,} courses")

    # Filter to IT-relevant categories
    df_it = df[df["category"].isin(IT_CATEGORIES)].copy()
    print(f"  After IT filter: {len(df_it):,} courses")

    # Drop rows with missing critical fields
    df_it = df_it.dropna(subset=["title", "url", "rating"])
    print(f"  After dropping nulls: {len(df_it):,} courses")

    # Filter to courses with meaningful ratings
    df_it = df_it[df_it["rating"] >= 4.0]
    df_it = df_it[df_it["num_reviews"] >= 50]
    print(f"  After quality filter (rating≥4.0, reviews≥50): {len(df_it):,} courses")

    # Build clean records
    courses = []
    for _, row in df_it.iterrows():
        courses.append({
            "title": str(row["title"]).strip(),
            "url": str(row["url"]).strip(),
            "platform": "Udemy",
            "type": "free" if row.get("is_paid") == False else "paid",
            "rating": round(float(row["rating"]), 1),
            "num_reviews": int(row.get("num_reviews", 0)),
            "num_subscribers": int(row.get("num_subscribers", 0)),
            "difficulty": str(row.get("instructional_level", "All Levels")).strip(),
            "category": str(row.get("category", "")).strip(),
            "headline": str(row.get("headline", "")).strip()[:200],
            # Search text for skill matching
            "_search": normalize(
                f"{row['title']} {row.get('headline', '')} {row.get('category', '')}"
            ),
        })

    print(f"  Final Udemy courses: {len(courses):,}")
    return courses


# ============================================================================
# COURSERA PROCESSING
# ============================================================================

def process_coursera(path: str) -> list:
    """Load, filter, and clean Coursera dataset."""
    print(f"\n[COURSERA] Loading {os.path.basename(path)}...")
    df = pd.read_csv(path, low_memory=False)
    print(f"  Raw: {len(df):,} courses")

    # Drop rows with missing critical fields
    df = df.dropna(subset=["Title", "course_url"])

    # Build clean records
    courses = []
    for _, row in df.iterrows():
        title = str(row["Title"]).strip()
        skills_raw = str(row.get("Skills", "")).strip()
        org = str(row.get("Organization", "")).strip()

        # Parse rating
        try:
            rating = float(str(row.get("Ratings", "0")).strip())
        except (ValueError, TypeError):
            rating = 0.0

        # Parse students enrolled (e.g. "700,909" → 700909)
        try:
            students_str = str(row.get("course_students_enrolled", "0"))
            students = int(students_str.replace(",", "").strip())
        except (ValueError, TypeError):
            students = 0

        # Parse skills into a list
        skills_list = [
            s.strip().lower()
            for s in skills_raw.split(",")
            if s.strip()
        ]

        courses.append({
            "title": title,
            "url": str(row["course_url"]).strip(),
            "platform": "Coursera",
            "type": str(row.get("Type", "Course")).strip(),
            "rating": rating,
            "organization": org,
            "difficulty": str(row.get("Difficulty", "All Levels")).strip(),
            "duration": str(row.get("Duration", "")).strip(),
            "num_students": students,
            "skills_list": skills_list,
            # Search text for skill matching
            "_search": normalize(f"{title} {org} {skills_raw}"),
        })

    print(f"  Final Coursera courses: {len(courses):,}")
    return courses


# ============================================================================
# SKILL → COURSE MATCHING
# ============================================================================

def build_skill_index(udemy_courses: list, coursera_courses: list) -> dict:
    """
    Build a lookup: skill → {udemy: [...], coursera: [...]}
    For each skill, find the best matching courses sorted by rating + popularity.
    """
    print("\n[INDEXING] Building skill → course lookup...")
    index = {}

    for skill in TARGET_SKILLS:
        udemy_matches = []
        coursera_matches = []

        # Match Udemy courses
        for course in udemy_courses:
            if text_contains_skill(course["_search"], skill):
                udemy_matches.append(course)

        # Match Coursera courses
        for course in coursera_courses:
            # Primary: check skills_list (exact match)
            skill_match = any(
                text_contains_skill(s, skill) or skill in s
                for s in course["skills_list"]
            )
            # Secondary: check search text
            text_match = text_contains_skill(course["_search"], skill)

            if skill_match or text_match:
                coursera_matches.append(course)

        # Sort Udemy: by (rating × log(subscribers)) — quality + popularity
        udemy_matches.sort(
            key=lambda c: c["rating"] * (c["num_subscribers"] ** 0.3),
            reverse=True,
        )

                # Sort Coursera: by rating + students
        coursera_matches.sort(
            key=lambda c: c["rating"] * (c.get("num_students", 0) ** 0.2),
            reverse=True,
        )

        # Take top 3 for each platform
        index[skill] = {
            "udemy": [
                {k: v for k, v in c.items() if not k.startswith("_")}
                for c in udemy_matches[:3]
            ],
            "coursera": [
                {k: v for k, v in c.items() if not k.startswith("_")}
                for c in coursera_matches[:3]
            ],
        }

        total = len(udemy_matches) + len(coursera_matches)
        if total > 0:
            print(f"  {skill:<30} → {len(udemy_matches):>3} Udemy, {len(coursera_matches):>3} Coursera")

    return index


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("  BUILDING COURSE DATABASE")
    print("=" * 70)

    # Process both datasets
    udemy_courses = process_udemy(UDEMY_CSV)
    coursera_courses = process_coursera(COURSERA_CSV)

    # Build skill index
    index = build_skill_index(udemy_courses, coursera_courses)

    # Stats
    skills_with_udemy = sum(1 for v in index.values() if v["udemy"])
    skills_with_coursera = sum(1 for v in index.values() if v["coursera"])
    skills_with_both = sum(
        1 for v in index.values() if v["udemy"] and v["coursera"]
    )
    skills_with_none = sum(
        1 for v in index.values() if not v["udemy"] and not v["coursera"]
    )

    print(f"\n{'=' * 70}")
    print(f"  SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Total skills indexed: {len(index)}")
    print(f"  Skills with Udemy courses: {skills_with_udemy}")
    print(f"  Skills with Coursera courses: {skills_with_coursera}")
    print(f"  Skills with BOTH: {skills_with_both}")
    print(f"  Skills with nothing (YouTube only): {skills_with_none}")

    # Save output
    output = {
        "metadata": {
            "total_skills": len(index),
            "udemy_courses_indexed": len(udemy_courses),
            "coursera_courses_indexed": len(coursera_courses),
            "skills_with_udemy": skills_with_udemy,
            "skills_with_coursera": skills_with_coursera,
        },
        "skills": index,
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    size_mb = os.path.getsize(OUTPUT_JSON) / 1024 / 1024
    print(f"\n  ✅ Saved: {OUTPUT_JSON}")
    print(f"  File size: {size_mb:.1f} MB")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()