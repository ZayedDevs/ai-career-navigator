import os
import re
import json
import sys
from datetime import datetime
from collections import Counter

import pandas as pd
import numpy as np

"""
Purpose:
    Transform raw LinkedIn job postings into clean, ML-ready datasets.
"""


# ============================================================================
# CONFIGURATION
# ============================================================================

# Path setup — relative to project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")

POSTINGS_FILE = os.path.join(RAW_DIR, "linkedin_job_postings.csv")
SKILLS_FILE = os.path.join(RAW_DIR, "job_skills.csv")

CLEANED_JOBS_OUT = os.path.join(PROCESSED_DIR, "cleaned_jobs.csv")
SKILL_CORPUS_OUT = os.path.join(PROCESSED_DIR, "skill_corpus.json")
REPORT_OUT = os.path.join(PROCESSED_DIR, "preprocessing_report.txt")

# Reproducibility
np.random.seed(42)

# Report log — accumulates messages then writes to file at end
report_log = []


# ============================================================================
# IT FILTERING CONFIG
# ============================================================================

# ============================================================================
# DOMAIN / NON-SKILL BLOCKLIST
# ============================================================================
# These terms appear in LinkedIn job postings as "skills" but are actually:
#   - Job domains/fields (not learnable skills)
#   - Academic disciplines (not skills)
#   - Generic words (not actionable)
#   - Years of experience junk
#   - Non-IT requirements (driver's license, citizenship, etc.)
#
# Filtering these produces a CLEAN, ACTIONABLE skill corpus for the user.

DOMAIN_BLOCKLIST = {
    # ── Pure domains/fields (you work in these, not learn them) ────────
    "data science", "data engineering", "data analytics",
    "software engineering", "software development",
    "software design", "software architecture",
    "database administration", "database design",
    "database architecture", "database security",
    "database management", "database maintenance",
    "database performance tuning", "database tuning",
    "cloud computing", "cloud architecture",
    "cloud infrastructure", "cloud security",
    "cloud services", "cloud native technologies",
    "cloudbased solutions", "cloud-based solutions",
    "cloud service technologies",
    "information technology", "information security",
    "information assurance", "information systems",
    "network engineering", "network administration",
    "network architecture", "network design",
    "network operations", "network management",
    "network monitoring", "network deployment",
    "network configuration", "network implementation",
    "network infrastructure", "network maintenance",
    "network analysis", "network performance",
    "network scaling", "network support",
    "devops engineering", "security engineering",
    "security operations", "security architecture",
    "security architecture reviews",
    "security monitoring", "security policies",
    "security risk assessments", "security controls",
    "systems engineering", "system administration",
    "systems administration", "server administration",
    "automation engineering", "test engineering",
    "site reliability engineering",
    "full stack development", "fullstack development",
    "full stack systems",
    "frontend development", "front end development",
    "backend development", "back end software engineering",
    "web development", "embedded systems",

    # ── Academic fields & degrees (not skills) ──────────────────────────
    "computer science", "computer engineering",
    "electrical engineering", "mechanical engineering",
    "engineering",
    "bachelor's degree", "master's degree", "phd",
    "high school diploma", "high school diploma or ged",
    "mathematics", "economics", "finance",
    "marketing", "nursing", "manufacturing",

    # ── Non-IT requirements ─────────────────────────────────────────────
    "driver's license", "valid driver's license",
    "u.s. citizenship", "covid19 vaccination",
    "fda approvals", "hand tools", "power tools",
    "regulated environment", "sales techniques",
    "mechanical knowledge", "email marketing",
    "business analysis",

    # ── Years of experience junk ────────────────────────────────────────
    "1+ years of people management experience",
    "2+ years of experience in agile practices",
    "3+ years of experience in open source frameworks",
    "4+ years of experience in open source frameworks",
    "4+ years of professional software engineering experience",
    "it experience",

    # ── Generic abstractions (too vague to be actionable) ───────────────
    "open source frameworks", "open source rdbms",
    "operating systems",
    "programming", "programming languages",
    "scripting languages",
    "data structures", "design patterns",
    "design", "configuration", "deployment",
    "monitoring", "documentation", "maintenance",
    "installation", "testing", "scalability",
    "availability", "integrity", "compliance",
    "innovation", "research", "training", "reporting",
    "analytics",
}


# Keywords that identify IT roles. Used in Stage 4 to filter the dataset.
IT_KEYWORDS = [
    # Software roles
    "software engineer", "software developer", "application developer",
    "frontend developer", "backend developer", "full stack", "fullstack",
    "full-stack", "front-end", "back-end", "web developer", "mobile developer",
    "ios developer", "android developer", "embedded software", "firmware engineer",
    "software architect",

    # Data roles
    "data scientist", "data analyst", "data engineer", "data architect",
    "machine learning engineer", "ml engineer", "ai engineer",
    "business intelligence", "bi developer", "bi analyst", "etl developer",

    # DevOps / Cloud / Infrastructure
    "devops", "cloud engineer", "cloud architect", "site reliability",
    "sre", "platform engineer", "infrastructure engineer",

    # Networking
    "network engineer", "network administrator", "network specialist",

    # Cybersecurity
    "cyber security", "cybersecurity", "security engineer", "security analyst",
    "information security", "infosec",

    # System admin / IT support
    "system administrator", "sysadmin", "it administrator",
    "it support", "it specialist", "it analyst",

    # Database
    "database administrator", "dba", "database engineer",

    # QA / Testing — REMOVED
    # Reason: LinkedIn's "QA Engineer" category was contaminated with
    # manufacturing/electrical test engineers (e.g., "electrical engineering"
    # appeared as a top skill). Excluded to maintain pure IT/software focus.

    # Solutions / Architect
    "solutions architect",

    # Programmer general
    "programmer",
]

# Negative keywords — even if title matches IT_KEYWORDS, exclude if these appear
EXCLUDE_KEYWORDS = [
    "sales", "marketing", "recruiter", "recruit", "hr manager",
    "account executive", "customer success",
    # Exclude QA/Test roles — data contamination with non-software QA
    "qa engineer", "test engineer", "quality engineer",
    "automation engineer", "sdet", "qa analyst",
    "quality assurance",
]


# ============================================================================
# ROLE CATEGORY MAPPING
# ============================================================================

# Maps detected keywords to broad role categories (your ML classifier labels).
# Order matters — first match wins. More specific keywords come first.
ROLE_CATEGORY_RULES = [
    # (search keyword, role category) — checked in order
    ("data scientist", "Data Scientist"),
    ("machine learning engineer", "Data Scientist"),
    ("ml engineer", "Data Scientist"),
    ("ai engineer", "Data Scientist"),

    ("data engineer", "Data Engineer"),
    ("etl developer", "Data Engineer"),
    ("big data", "Data Engineer"),

    ("data analyst", "Data Analyst"),
    ("business intelligence", "Data Analyst"),
    ("bi analyst", "Data Analyst"),
    ("bi developer", "Data Analyst"),
    ("reporting analyst", "Data Analyst"),

    ("devops", "DevOps Engineer"),
    ("site reliability", "DevOps Engineer"),
    ("sre", "DevOps Engineer"),
    ("cloud engineer", "DevOps Engineer"),
    ("cloud architect", "DevOps Engineer"),
    ("platform engineer", "DevOps Engineer"),

    ("frontend", "Frontend Developer"),
    ("front-end", "Frontend Developer"),
    ("front end", "Frontend Developer"),
    ("ui developer", "Frontend Developer"),
    ("react developer", "Frontend Developer"),

    ("backend", "Backend Developer"),
    ("back-end", "Backend Developer"),
    ("back end", "Backend Developer"),
    ("api developer", "Backend Developer"),

    ("full stack", "Software Engineer"),
    ("fullstack", "Software Engineer"),
    ("full-stack", "Software Engineer"),

    ("mobile developer", "Software Engineer"),
    ("ios developer", "Software Engineer"),
    ("android developer", "Software Engineer"),
    ("web developer", "Software Engineer"),
    ("software engineer", "Software Engineer"),
    ("software developer", "Software Engineer"),
    ("application developer", "Software Engineer"),
    ("software architect", "Software Engineer"),

    ("network engineer", "Network Engineer"),
    ("network administrator", "Network Engineer"),
    ("network specialist", "Network Engineer"),

    ("cyber security", "Cybersecurity Analyst"),
    ("cybersecurity", "Cybersecurity Analyst"),
    ("security engineer", "Cybersecurity Analyst"),
    ("security analyst", "Cybersecurity Analyst"),
    ("information security", "Cybersecurity Analyst"),
    ("infosec", "Cybersecurity Analyst"),

    ("system administrator", "System Administrator"),
    ("sysadmin", "System Administrator"),
    ("it administrator", "System Administrator"),
    ("it support", "System Administrator"),
    ("it specialist", "System Administrator"),

    ("database administrator", "Database Administrator"),
    ("dba", "Database Administrator"),

    # QA Engineer category removed — data contamination
    # ("qa engineer", "QA Engineer"),
    # ("test engineer", "QA Engineer"),
    # ("automation engineer", "QA Engineer"),
    # ("sdet", "QA Engineer"),

    # Generic fallback for any remaining programmer/developer
    ("programmer", "Software Engineer"),
]


# ============================================================================
# JOB LEVEL DERIVATION
# ============================================================================

SENIOR_KEYWORDS = [
    "senior", "sr.", "sr ", "lead", "principal", "staff",
    "head of", "director", "vp ", "chief", "manager",
    " iii", " iv", " v ",
]

ENTRY_KEYWORDS = [
    "junior", "jr.", "jr ", "intern", "trainee", "graduate",
    "entry", "associate", "apprentice", " i ", " ii",
]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def log(msg):
    """Print to terminal AND save to report log."""
    print(msg)
    report_log.append(msg)


def section(title):
    """Print a visual section header."""
    sep = "=" * 78
    log(f"\n{sep}")
    log(f"  {title}")
    log(sep)


# ============================================================================
# PIPELINE STAGES
# ============================================================================

def stage_1_load_data():
    """
    Stage 1: Load raw CSV files and select only the columns we need.
    This drastically reduces memory usage from the start.
    """
    section("STAGE 1 — LOAD RAW DATA")

    # Verify files exist
    if not os.path.exists(POSTINGS_FILE):
        log(f"❌ ERROR: Cannot find {POSTINGS_FILE}")
        sys.exit(1)
    if not os.path.exists(SKILLS_FILE):
        log(f"❌ ERROR: Cannot find {SKILLS_FILE}")
        sys.exit(1)

    # Only load the columns we actually need — saves RAM
    postings_cols = ["job_link", "job_title", "company", "job_location"]
    log(f"Loading: {os.path.basename(POSTINGS_FILE)}")
    log(f"  Selected columns: {postings_cols}")
    df_postings = pd.read_csv(
        POSTINGS_FILE,
        usecols=postings_cols,
        engine="python",
        on_bad_lines="skip"
    )
    log(f"  ✓ Loaded {len(df_postings):,} rows")

    log(f"\nLoading: {os.path.basename(SKILLS_FILE)}")
    df_skills = pd.read_csv(
        SKILLS_FILE,
        engine="python",
        on_bad_lines="skip"
    )
    log(f"  ✓ Loaded {len(df_skills):,} rows")

    return df_postings, df_skills


def stage_2_merge(df_postings, df_skills):
    """
    Stage 2: Merge postings with skills on job_link.
    Inner join discards any job that doesn't have skills data.
    """
    section("STAGE 2 — MERGE ON job_link")

    log(f"Postings rows: {len(df_postings):,}")
    log(f"Skills rows:   {len(df_skills):,}")

    df = df_postings.merge(df_skills, on="job_link", how="inner")
    log(f"\n✓ Merged dataset: {len(df):,} rows")
    log(f"  Lost {len(df_postings) - len(df):,} jobs that had no skills data")

    return df


def stage_3_clean_missing_duplicates(df):
    """
    Stage 3: Remove rows with missing critical data, and deduplicate.
    """
    section("STAGE 3 — CLEAN MISSING VALUES & DUPLICATES")

    start = len(df)

    # Drop rows where skills are missing
    df = df.dropna(subset=["job_skills", "job_title"])
    log(f"After dropping null skills/titles: {len(df):,} rows  (-{start - len(df):,})")

    # Drop duplicates by job_link (same job posted multiple times)
    pre_dedup = len(df)
    df = df.drop_duplicates(subset=["job_link"])
    log(f"After dropping duplicate job_links: {len(df):,} rows  (-{pre_dedup - len(df):,})")

    # Also dedupe by (title + skills) combo — different links but same job
    pre_dedup = len(df)
    df = df.drop_duplicates(subset=["job_title", "job_skills"])
    log(f"After dropping title+skills dupes:  {len(df):,} rows  (-{pre_dedup - len(df):,})")

    return df.reset_index(drop=True)


def stage_4_filter_it_roles(df):
    """
    Stage 4: Keep only IT-related jobs based on title keywords.
    """
    section("STAGE 4 — FILTER IT ROLES ONLY")

    # Build regex patterns
    include_pattern = "|".join(re.escape(k) for k in IT_KEYWORDS)
    exclude_pattern = "|".join(re.escape(k) for k in EXCLUDE_KEYWORDS)

    title_lower = df["job_title"].astype(str).str.lower()

    matches_it = title_lower.str.contains(include_pattern, regex=True, na=False)
    matches_exclude = title_lower.str.contains(exclude_pattern, regex=True, na=False)

    is_it_role = matches_it & ~matches_exclude

    log(f"IT-keyword matches:  {matches_it.sum():,}")
    log(f"Excluded (sales/HR/etc): {(matches_it & matches_exclude).sum():,}")
    log(f"Final IT jobs:       {is_it_role.sum():,}")

    return df[is_it_role].reset_index(drop=True)


def map_role_category(title):
    """Map a job title to one of the broad role categories. Returns None if no match."""
    title_lower = str(title).lower()
    for keyword, category in ROLE_CATEGORY_RULES:
        if keyword in title_lower:
            return category
    return None


def derive_job_level(title):
    """Determine Entry/Mid/Senior from title keywords. Default = Mid."""
    title_lower = str(title).lower()

    # Check senior first (higher priority)
    for kw in SENIOR_KEYWORDS:
        if kw in title_lower:
            return "Senior"

    # Then check entry
    for kw in ENTRY_KEYWORDS:
        if kw in title_lower:
            return "Entry"

    # Default
    return "Mid"


def stage_5_normalize_titles_and_levels(df):
    """
    Stage 5: Add role_category and job_level columns.
    """
    section("STAGE 5 — NORMALIZE TITLES & DERIVE LEVELS")

    log("Mapping job titles to role categories...")
    df["role_category"] = df["job_title"].apply(map_role_category)

    # Drop rows that didn't match any category
    pre = len(df)
    df = df.dropna(subset=["role_category"]).reset_index(drop=True)
    log(f"  Dropped {pre - len(df):,} jobs that didn't match a category")
    log(f"  Remaining: {len(df):,} jobs\n")

    log("Role category distribution:")
    role_counts = df["role_category"].value_counts()
    for role, count in role_counts.items():
        log(f"  {role:<25} {count:>6,}")

    log("\nDeriving job levels from title keywords...")
    df["job_level"] = df["job_title"].apply(derive_job_level)

    log("\nJob level distribution:")
    for level, count in df["job_level"].value_counts().items():
        log(f"  {level:<10} {count:>6,}")

    return df


def clean_skill(skill):
    """Standardize a single skill string."""
    s = str(skill).strip().lower()
    # Collapse multiple whitespaces
    s = re.sub(r"\s+", " ", s)
    # Remove leading/trailing punctuation
    s = s.strip(".,;:-")
    return s


def parse_skills(skills_str):
    """
    Parse comma-separated skill string into clean deduplicated list.
    Also filters out domain/non-skill noise via DOMAIN_BLOCKLIST.
    """
    if pd.isna(skills_str):
        return []

    skills = [clean_skill(s) for s in str(skills_str).split(",")]
    # Remove empty strings and very short noise (1-2 char tokens)
    skills = [s for s in skills if len(s) >= 2]

    # Filter out domain/non-skill entries
    skills = [s for s in skills if s not in DOMAIN_BLOCKLIST]

    # Deduplicate while preserving order
    seen = set()
    result = []
    for s in skills:
        if s not in seen:
            seen.add(s)
            result.append(s)
    return result


def stage_6_clean_skills(df):
    """
    Stage 6: Parse and clean the job_skills column.
    """
    section("STAGE 6 — CLEAN & STANDARDIZE SKILLS")

    log("Parsing skill strings into clean lists...")
    df["skills_list"] = df["job_skills"].apply(parse_skills)
    df["skill_count"] = df["skills_list"].apply(len)

    # Drop jobs with no skills after cleaning
    pre = len(df)
    df = df[df["skill_count"] > 0].reset_index(drop=True)
    log(f"  Dropped {pre - len(df):,} jobs with empty skills after cleaning")

    # Replace job_skills with cleaned comma-separated version
    df["job_skills"] = df["skills_list"].apply(lambda lst: ", ".join(lst))

    log(f"\nSkill statistics:")
    log(f"  Min skills per job:    {df['skill_count'].min()}")
    log(f"  Max skills per job:    {df['skill_count'].max()}")
    log(f"  Mean skills per job:   {df['skill_count'].mean():.1f}")
    log(f"  Median skills per job: {df['skill_count'].median():.0f}")

    return df


def stage_7_export(df):
    """
    Stage 7: Save final outputs and generate the skill corpus.
    """
    section("STAGE 7 — EXPORT PROCESSED DATA")

    # Ensure output directory exists
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # ----- Output 1: cleaned_jobs.csv -----
    final_cols = [
        "job_title", "role_category", "job_level",
        "company", "job_location",
        "job_skills", "skill_count"
    ]
    df_final = df[final_cols]
    df_final.to_csv(CLEANED_JOBS_OUT, index=False)
    log(f"✓ Saved: {CLEANED_JOBS_OUT}")
    log(f"  Rows: {len(df_final):,}")
    log(f"  Columns: {list(df_final.columns)}")

    # ----- Output 2: skill_corpus.json -----
    log("\nBuilding skill corpus (role → skills mapping)...")
    corpus = {}
    for role in df["role_category"].unique():
        role_df = df[df["role_category"] == role]

        # Flatten all skills from all jobs in this role
        all_skills = []
        for skills in role_df["skills_list"]:
            all_skills.extend(skills)

        # Count frequency
        freq_counter = Counter(all_skills)
        # Keep top 100 most frequent
        top_skills = freq_counter.most_common(100)

        corpus[role] = {
            "job_count": int(len(role_df)),
            "unique_skills_total": int(len(freq_counter)),
            "top_skills": [s for s, _ in top_skills],
            "skill_frequency": {s: int(c) for s, c in top_skills}
        }

    with open(SKILL_CORPUS_OUT, "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2)
    log(f"\n✓ Saved: {SKILL_CORPUS_OUT}")
    log(f"  Roles in corpus: {len(corpus)}")

    return df_final


def write_report():
    """Write the accumulated log to the report file."""
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    header = (
        "AI Career Navigator — Preprocessing Report\n"
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Student: Zayed Khaled (B032310764) | UTeM FAIX\n"
        + "=" * 78 + "\n"
    )
    with open(REPORT_OUT, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(report_log))
    print(f"\n📄 Report saved: {REPORT_OUT}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "=" * 78)
    print("  AI CAREER NAVIGATOR — DATA PREPROCESSING PIPELINE")
    print("=" * 78)

    start_time = datetime.now()

    df_postings, df_skills = stage_1_load_data()
    df = stage_2_merge(df_postings, df_skills)
    df = stage_3_clean_missing_duplicates(df)
    df = stage_4_filter_it_roles(df)
    df = stage_5_normalize_titles_and_levels(df)
    df = stage_6_clean_skills(df)
    df_final = stage_7_export(df)

    elapsed = (datetime.now() - start_time).total_seconds()

    section("PIPELINE COMPLETE")
    log(f"Total time:    {elapsed:.1f} seconds")
    log(f"Final dataset: {len(df_final):,} IT job records")
    log(f"\nNext step: Train ML models in ml/training/")

    write_report()


if __name__ == "__main__":
    main()