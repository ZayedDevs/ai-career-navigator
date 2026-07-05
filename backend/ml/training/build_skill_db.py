import os
import json
import joblib
from datetime import datetime

"""
Purpose:
    Build a master IT skills database from the role-based skill corpus.
    This database is used by the Skill Extractor to identify skills in
    user resumes (Layer 1: Dictionary Lookup).
"""

# ============================================================================
# DOMAIN / NON-SKILL BLOCKLIST
# ============================================================================
# (Synced with preprocess_data.py — keep both in sync if you change one)

DOMAIN_BLOCKLIST = {
    # Pure domains/fields
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

    # Academic fields & degrees
    "computer science", "computer engineering",
    "electrical engineering", "mechanical engineering",
    "engineering",
    "bachelor's degree", "master's degree", "phd",
    "high school diploma", "high school diploma or ged",
    "mathematics", "economics", "finance",
    "marketing", "nursing", "manufacturing",

    # Non-IT requirements
    "driver's license", "valid driver's license",
    "u.s. citizenship", "covid19 vaccination",
    "fda approvals", "hand tools", "power tools",
    "regulated environment", "sales techniques",
    "mechanical knowledge", "email marketing",
    "business analysis",

    # Years of experience junk
    "1+ years of people management experience",
    "2+ years of experience in agile practices",
    "3+ years of experience in open source frameworks",
    "4+ years of experience in open source frameworks",
    "4+ years of professional software engineering experience",
    "it experience",

    # Generic abstractions
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

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

CORPUS_FILE = os.path.join(PROJECT_ROOT, "data", "processed", "skill_corpus.json")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "ml", "saved_models", "skill_database.pkl")


# ============================================================================
# MANUAL SKILL ALIASES
# ============================================================================
# Maps variations to their canonical (preferred) form.
# This handles spelling variations that the model sees as different but
# are actually the same skill in real life.

SKILL_ALIASES = {
    # Programming languages
    "javascript": "javascript",
    "js": "javascript",
    "ecmascript": "javascript",

    "typescript": "typescript",
    "ts": "typescript",

    "node": "node.js",
    "nodejs": "node.js",
    "node.js": "node.js",
    "node js": "node.js",

    "python": "python",
    "python3": "python",
    "python 3": "python",

    "c++": "c++",
    "cpp": "c++",

    "c#": "c#",
    "csharp": "c#",
    "c sharp": "c#",

    "golang": "go",
    "go lang": "go",

    # Frameworks
    "reactjs": "react",
    "react.js": "react",
    "react js": "react",

    "angularjs": "angular",
    "angular.js": "angular",
    "angular js": "angular",

    "vuejs": "vue",
    "vue.js": "vue",

    # Cloud
    "amazon web services": "aws",
    "aws cloud": "aws",

    "google cloud platform": "gcp",
    "google cloud": "gcp",

    "microsoft azure": "azure",
    "azure cloud": "azure",

    # Databases — SQL family all map to canonical "sql"
    # Rationale: MySQL/PostgreSQL users know SQL; gap analyzer
    # should not penalize them for "missing sql" when they have a dialect.
    "mysql": "sql",
    "my sql": "sql",
    "postgresql": "sql",
    "postgres": "sql",
    "postgre sql": "sql",
    "sqlite": "sql",
    "sqlite3": "sql",
    "ms sql": "sql",
    "mssql": "sql",
    "sql server": "sql",
    "microsoft sql server": "sql",
    "mariadb": "sql",
    "t-sql": "sql",
    "plsql": "sql",
    "pl/sql": "sql",

    # Oracle stays separate (specialized enough to be distinct)
    "oracle": "oracle database",
    "oracle db": "oracle database",
    "oracle sql": "oracle database",

    # ML/Data
    "machine learning": "machine learning",
    "ml": "machine learning",

    "artificial intelligence": "ai",
    "ai/ml": "machine learning",

    "deep learning": "deep learning",
    "dl": "deep learning",

    "natural language processing": "nlp",
    "natural language": "nlp",

    "tensor flow": "tensorflow",
    "tf": "tensorflow",

    "py torch": "pytorch",

    "scikitlearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",

    # DevOps
    "k8s": "kubernetes",
    "kube": "kubernetes",

    "ci cd": "ci/cd",
    "cicd": "ci/cd",
    "continuous integration": "ci/cd",
    "continuous deployment": "ci/cd",

    "infrastructure as code": "iac",

    # Soft skills (normalize variations)
    "problem solving": "problem solving",
    "problemsolving": "problem solving",
    "problem-solving": "problem solving",

    "communication skills": "communication",
    "verbal communication": "communication",
    "written communication": "communication",

    # Misc
    "rest api": "rest api",
    "restful api": "rest api",
    "restful apis": "rest api",
    "rest apis": "rest api",
    "restful web services": "rest api",

    "html/css": "html",  # We'll add CSS separately
}


# ============================================================================
# MANUAL CURATED ADDITIONS
# ============================================================================
# Common IT skills that may not be top 100 in any role but are still relevant.

EXTRA_SKILLS = [
    # Languages
    "c", "rust", "kotlin", "swift", "php", "ruby", "perl", "scala", "r",
    "matlab", "bash", "shell", "powershell",

    # Web stacks
    "express", "fastapi", "flask", "django", "spring boot", "spring",
    "rails", "laravel", "next.js", "nuxt.js", "svelte",

    # Mobile
    "react native", "flutter", "ionic", "xamarin",

    # Databases
    "mongodb", "redis", "elasticsearch", "cassandra", "dynamodb",
    "neo4j", "firebase", "supabase",

    # Cloud services
    "lambda", "ec2", "s3", "rds", "cloudfront", "cloudformation",
    "azure functions", "google cloud functions",

    # DevOps tools
    "github actions", "gitlab ci", "circleci", "travis ci",
    "argocd", "helm", "istio", "prometheus", "grafana", "elk stack",
    "splunk", "datadog", "new relic",

    # Data tools
    "airflow", "databricks", "snowflake", "tableau", "power bi",
    "looker", "metabase", "superset", "dbt", "great expectations",

    # ML/AI
    "huggingface", "transformers", "langchain", "openai", "llm",
    "rag", "vector database", "pinecone", "weaviate", "chromadb",
    "mlflow", "kubeflow", "weights and biases", "wandb",

    # Security
    "owasp", "burp suite", "metasploit", "nmap", "wireshark",
    "kali linux", "splunk", "soc", "siem", "ids", "ips",
    "penetration testing", "vulnerability assessment", "cissp",
    "ceh", "comptia security+", "iso 27001", "gdpr", "hipaa",

    # Networking
    "ccna", "ccnp", "ccie", "bgp", "ospf", "vlan", "vpn",
    "firewall", "load balancer", "cdn", "dns", "dhcp", "nat",
    "subnetting", "routing", "switching",

    # Methodologies
    "agile", "scrum", "kanban", "waterfall", "devops", "tdd",
    "bdd", "pair programming", "code review", "git flow",

    # Soft skills
    "leadership", "teamwork", "collaboration", "mentoring",
    "problem solving", "critical thinking", "time management",
    "project management", "stakeholder management",
]


# ============================================================================
# MAIN BUILDER
# ============================================================================

def build_database():
    print("\n" + "=" * 78)
    print("  BUILDING MASTER SKILL DATABASE")
    print("=" * 78)

    # 1. Load the role-based skill corpus
    print(f"\nLoading: {os.path.basename(CORPUS_FILE)}")
    if not os.path.exists(CORPUS_FILE):
        print(f"❌ ERROR: {CORPUS_FILE} not found.")
        print("   Run preprocess_data.py first.")
        return

    with open(CORPUS_FILE, "r", encoding="utf-8") as f:
        corpus = json.load(f)

    print(f"✓ Loaded {len(corpus)} role categories")

    # 2. Collect all top skills from all roles
    print("\nCollecting top skills from all roles...")
    all_skills = set()
    for role, data in corpus.items():
        role_skills = data["top_skills"]
        all_skills.update(role_skills)
        print(f"  {role:<25} {len(role_skills):>3} skills")

    print(f"\n✓ Total unique skills from corpus: {len(all_skills):,}")

    # 3. Add extra curated skills
    print(f"\nAdding {len(EXTRA_SKILLS)} manually curated extra skills...")
    before = len(all_skills)
    for skill in EXTRA_SKILLS:
        all_skills.add(skill.lower())
    added = len(all_skills) - before
    print(f"✓ Added {added} new skills not in corpus")

    # 4. Apply alias normalization
    print(f"\nNormalizing aliases ({len(SKILL_ALIASES)} mappings defined)...")

    # Step 4a: build the alias map (lowercase keys)
    alias_map = {k.lower(): v.lower() for k, v in SKILL_ALIASES.items()}

    # Step 4b: normalize all skills through the alias map
    canonical_skills = set()
    for skill in all_skills:
        normalized = alias_map.get(skill.lower(), skill.lower())
        canonical_skills.add(normalized)

    print(f"✓ Canonical skills after alias normalization: {len(canonical_skills):,}")

    # 4.5 Collapse common variants into canonical forms
    print("\nCollapsing skill variants (agile methodology → agile, etc.)...")

    # When a skill contains these "base" words plus extra wording,
    # we collapse it to the base skill.
    variant_collapse_rules = {
        "agile": ["agile methodology", "agile methodologies", "agile practices",
                  "agile development", "agile development practices",
                  "agile engineering practices"],
        "scrum": ["scrum methodology", "scrum practices"],
        "communication": ["communication skills", "verbal communication",
                          "written communication", "oral communication"],
        "problem solving": ["problem-solving", "problemsolving",
                            "problem solving skills", "problem resolution",
                            "problemsolving skills"],
        "leadership": ["leadership skills", "team leadership"],
        "teamwork": ["team work", "team player", "teamwork skills"],
        "rest api": ["rest apis", "restful api", "restful apis",
                     "restful web services", "rest web services"],
        "machine learning": ["ml", "machine-learning"],
        "deep learning": ["dl", "deep-learning"],
        "ci/cd": ["ci cd", "cicd", "continuous integration",
                  "continuous deployment", "continuous integration/continuous deployment"],
        "data analysis": ["data analytics"],
        "data visualization": ["data viz", "data visualisation"],
        "etl": ["etl/elt", "extract transform load"],
        "nosql": ["nosql databases", "no sql"],
        "sql": ["sql databases", "sql server"],
    }

    # Build reverse map: variant → canonical
    variant_map = {}
    for canonical, variants in variant_collapse_rules.items():
        for variant in variants:
            variant_map[variant.lower()] = canonical.lower()

    collapsed = set()
    collapse_count = 0
    for skill in canonical_skills:
        if skill.lower() in variant_map:
            collapsed.add(variant_map[skill.lower()])
            collapse_count += 1
        else:
            collapsed.add(skill)

    canonical_skills = collapsed
    print(f"  Collapsed {collapse_count} variants into canonical forms")
    print(f"  Skills after variant collapse: {len(canonical_skills):,}")

    # 5. Filter out noise — multiple filters for cleaner skill list
    print("\nFiltering noise (junk patterns, experience phrases, etc.)...")
    before = len(canonical_skills)

    # Junk patterns — entries matching these are NOT real skills
    import re
    junk_patterns = [
        r"^\d+\+?\s*year",              # "3+ years..."
        r"^\d+\+?\s*month",              # "6+ months..."
        r"^\d+\+?\s*y[er]\b",            # "3 yr..."
        r"\byears? of experience\b",     # "years of experience"
        r"\bmonths? of experience\b",    # "months of experience"
        r"^experience (in|with|of)\b",   # "experience in..."
        r"^knowledge (in|of|with)\b",    # "knowledge of..."
        r"^understanding (of|in)\b",     # "understanding of..."
        r"^familiarity (with|in)\b",     # "familiarity with..."
        r"^ability to\b",                # "ability to..."
        r"^proficient (in|with)\b",      # "proficient in..."
        r"^demonstrated\b",              # "demonstrated..."
        r"^proven\b",                    # "proven..."
        r"^strong\b",                    # "strong..."
        r"^excellent\b",                 # "excellent..."
        r"^solid\b",                     # "solid..."
        r"^working knowledge\b",         # "working knowledge..."
        r"^hands.?on\b",                 # "hands-on..."
        r"^willingness\b",               # "willingness..."
        r"^passion(ate)?\b",             # "passion..."
        r"^bachelor",                    # "bachelor's degree"
        r"^master",                      # "master's degree"
        r"^phd\b",                       # "phd"
        r"^degree\b",                    # "degree in..."
        r"^certification\b",             # generic "certification"
        r"\bdegree\b",                   # contains "degree"
    ]

    cleaned = set()
    removed = []
    for skill in canonical_skills:
        # Reject if matches any junk pattern
        is_junk = any(re.search(p, skill, re.IGNORECASE) for p in junk_patterns)

        # Reject if too long or all digits
        # Note: We allow 1-char skills only for known programming languages
        if len(skill) > 40 or skill.isdigit():
            is_junk = True

        # Reject single-character entries EXCEPT known languages
        single_char_languages = {"r", "c"}  # R and C are real languages
        if len(skill) == 1 and skill.lower() not in single_char_languages:
            is_junk = True

        # Reject if it's just generic adjectives/nouns with no IT meaning
        if skill in {"experience", "knowledge", "skills", "ability", "expertise"}:
            is_junk = True

        # Reject if it contains too many words (likely a phrase, not a skill)
        if len(skill.split()) > 5:
            is_junk = True

        if is_junk:
            removed.append(skill)
        else:
            cleaned.add(skill)

    canonical_skills = cleaned
    print(f"  Removed {before - len(canonical_skills)} junk entries")
    print(f"  Remaining canonical skills: {len(canonical_skills):,}")

    # Optional: show what got removed (debugging aid)
    if removed:
        print(f"\n  Sample of removed junk (first 10):")
        for r in sorted(removed)[:10]:
            print(f"    ✗ {r}")

    # 5.5 Filter out domain words / non-skills
    print("\nFiltering domain words (data science, software engineering, etc.)...")
    before = len(canonical_skills)
    canonical_skills = canonical_skills - DOMAIN_BLOCKLIST
    print(f"  Removed {before - len(canonical_skills)} domain/non-skill entries")
    print(f"  Final canonical skills: {len(canonical_skills):,}")


    # 6. Build final database
    database = {
        "canonical_skills": canonical_skills,
        "alias_map": alias_map,
        "skill_count": len(canonical_skills),
        "built_at": datetime.now().isoformat(),
        "source": "linkedin_jobs_corpus + manual curation",
    }

    # 7. Save
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    joblib.dump(database, OUTPUT_FILE)

    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"\n✓ Saved: {OUTPUT_FILE}")
    print(f"  File size:         {size_kb:.1f} KB")
    print(f"  Canonical skills:  {len(canonical_skills):,}")
    print(f"  Alias mappings:    {len(alias_map):,}")

    # 8. Show sample
    print("\nSample of canonical skills (first 30 sorted):")
    sample = sorted(canonical_skills)[:30]
    for s in sample:
        print(f"  • {s}")

    print("\n" + "=" * 78)
    print("  COMPLETE — skill database ready for use by Skill Extractor")
    print("=" * 78)


if __name__ == "__main__":
    build_database()