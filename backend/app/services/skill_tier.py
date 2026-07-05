from functools import lru_cache


# ============================================================================
# TIER DEFINITIONS — Manual curation for accuracy
# ============================================================================
# This is the "human intelligence" baked into the system.
# Real production career platforms also have curated tier mappings.
# Skills NOT in any tier set fall back to the keyword-based classifier below.

"""
Purpose:
    Classify each skill into a learning tier (Foundation/Intermediate/Advanced)
    and estimate the time required to learn it.

    This drives the Roadmap Generator's phase ordering.
"""



FOUNDATION_SKILLS = {
    # Programming languages (must learn first)
    "python", "java", "javascript", "c", "c++", "c#", "go",
    "ruby", "php", "kotlin", "swift", "scala", "r", "typescript",

    # Core web tech
    "html", "css", "sql",

    # Version control & tools
    "git", "github", "gitlab", "bitbucket",

    # OS fundamentals
    "linux", "bash", "shell", "powershell", "unix",

    # Core methodologies
    "agile", "scrum", "version control",

    # Foundational data concepts
    "data analysis", "statistics", "probability",

    # Soft skills (always foundational)
    "communication", "teamwork", "problem solving",
    "critical thinking", "leadership", "collaboration",
    "adaptability", "analytical skills", "analytical thinking",
    "attention to detail", "time management",
}


INTERMEDIATE_SKILLS = {
    # Frontend frameworks
    "react", "angular", "vue", "vue.js", "svelte", "next.js", "nuxt.js",
    "jquery", "redux", "tailwind", "bootstrap", "sass",

    # Backend frameworks
    "node.js", "express", "flask", "django", "fastapi",
    "spring", "spring boot", "rails", "laravel", ".net",

    # Mobile
    "react native", "flutter", "ionic", "xamarin",

    # ML/Data libraries
    "pandas", "numpy", "scikit-learn", "matplotlib", "seaborn",
    "tensorflow", "pytorch", "keras",

    # Databases
    "mysql", "postgresql", "mongodb", "sqlite",
    "redis", "sqlite3", "sql server", "oracle",

    # Web/API concepts
    "rest api", "graphql", "websockets", "soap", "api integration",

    # Testing
    "unit testing", "integration testing", "pytest",
    "junit", "jest", "mocha", "selenium",

    # Data viz
    "tableau", "power bi", "data visualization", "looker",

    # Build/Package tools
    "npm", "yarn", "pip", "maven", "gradle", "webpack",

    # Cloud basics
    "aws", "azure", "gcp",

    # Containerization basics
    "docker",

    # Authentication
    "oauth", "jwt", "authentication", "authorization",

    # CI basics
    "ci/cd",

    # Data tools
    "etl", "airflow", "snowflake", "databricks",

    # Networking concepts
    "tcp/ip", "dns", "http", "https", "networking",
}


ADVANCED_SKILLS = {
    # Container orchestration
    "kubernetes", "k8s", "helm", "istio", "rancher",

    # Infrastructure as Code
    "terraform", "ansible", "puppet", "chef", "cloudformation",

    # ML/AI specialized
    "deep learning", "machine learning", "computer vision",
    "natural language processing", "nlp", "reinforcement learning",
    "transformers", "huggingface", "langchain", "llm", "rag",
    "computer vision", "neural networks",

    # Big Data
    "spark", "hadoop", "kafka", "hive", "pig", "flink",
    "apache spark", "big data",

    # Microservices / Architecture
    "microservices", "service mesh", "event-driven architecture",
    "serverless", "lambda", "kafka",

    # Cloud advanced services
    "ec2", "s3", "rds", "cloudfront", "route 53",
    "azure functions", "cloud architecture",

    # Security advanced
    "penetration testing", "owasp", "siem", "ids", "ips",
    "cissp", "ceh", "incident response", "threat hunting",
    "vulnerability assessment", "burp suite", "metasploit",
    "kali linux", "splunk",

    # Networking advanced
    "bgp", "ospf", "mpls", "ccna", "ccnp", "ccie",
    "routing", "switching", "subnetting", "vlan", "vpn",
    "firewall", "load balancer", "cdn",

    # DevOps advanced
    "jenkins", "github actions", "gitlab ci", "argocd",
    "prometheus", "grafana", "elk stack", "datadog",
    "site reliability", "sre", "monitoring", "observability",

    # Data Engineering
    "data engineering", "data warehouse", "data lake",
    "data modeling", "dbt", "data pipeline",

    # Database advanced
    "database administration", "performance tuning",
    "indexing", "replication", "sharding",

    # Architecture
    "system design", "distributed systems",
    "scalability", "high availability",
}


# ============================================================================
# CATEGORY MAPPING — Used for display grouping
# ============================================================================

CATEGORY_KEYWORDS = {
    "language": {"python", "java", "javascript", "c", "c++", "c#", "go",
                 "ruby", "php", "kotlin", "swift", "scala", "r", "typescript",
                 "rust", "perl", "bash", "shell", "powershell"},

    "frontend": {"html", "css", "react", "angular", "vue", "vue.js",
                 "svelte", "next.js", "nuxt.js", "jquery", "redux",
                 "tailwind", "bootstrap", "sass", "less"},

    "backend": {"node.js", "express", "flask", "django", "fastapi",
                "spring", "spring boot", "rails", "laravel", ".net",
                "rest api", "graphql", "soap"},

    "database": {"sql", "mysql", "postgresql", "mongodb", "sqlite",
                 "redis", "oracle", "sql server", "nosql",
                 "database administration", "indexing"},

    "ml_ai": {"machine learning", "deep learning", "computer vision",
              "nlp", "natural language processing", "tensorflow", "pytorch",
              "keras", "scikit-learn", "pandas", "numpy", "matplotlib",
              "neural networks", "huggingface", "transformers", "llm"},

    "cloud": {"aws", "azure", "gcp", "ec2", "s3", "lambda",
              "cloud architecture", "serverless"},

    "devops": {"docker", "kubernetes", "k8s", "terraform", "ansible",
               "jenkins", "ci/cd", "github actions", "gitlab ci",
               "prometheus", "grafana", "site reliability"},

    "security": {"penetration testing", "cybersecurity", "owasp",
                 "siem", "cissp", "ceh", "incident response",
                 "vulnerability assessment", "encryption", "authentication"},

    "data_eng": {"spark", "hadoop", "kafka", "airflow", "snowflake",
                 "databricks", "etl", "data warehouse", "data lake",
                 "big data", "data pipeline"},

    "networking": {"tcp/ip", "dns", "http", "bgp", "ospf", "ccna",
                   "routing", "switching", "subnetting", "vlan",
                   "vpn", "firewall", "networking"},

    "soft_skills": {"communication", "teamwork", "problem solving",
                    "critical thinking", "leadership", "collaboration",
                    "adaptability", "analytical thinking",
                    "attention to detail", "time management"},

    "methodology": {"agile", "scrum", "kanban", "tdd", "version control",
                    "git", "github"},

    "tools": {"jira", "confluence", "slack", "notion", "figma"},
}


# ============================================================================
# WEEKS ESTIMATES — Based on tier
# ============================================================================
# These are conservative averages for a motivated learner spending ~10 hrs/week.

TIER_WEEKS = {
    1: 2,   # Foundation: 2 weeks average (easy concepts, lots of resources)
    2: 3,   # Intermediate: 3 weeks (frameworks need practice)
    3: 5,   # Advanced: 5 weeks (deep concepts, complex tools)
}


# ============================================================================
# KEYWORD-BASED FALLBACK CLASSIFIER
# ============================================================================
# Used when a skill is not in any curated set.
# Inspects skill name for hints about complexity.

ADVANCED_HINTS = [
    "advanced", "architecture", "engineering", "administration",
    "design patterns", "scaling", "distributed", "orchestration",
    "high availability", "fault tolerance",
]

INTERMEDIATE_HINTS = [
    "framework", "library", "api", "testing", "automation",
    "deployment", "monitoring",
]


def _fallback_tier(skill: str) -> int:
    """Heuristic tier assignment for uncurated skills."""
    skill_lower = skill.lower()
    if any(hint in skill_lower for hint in ADVANCED_HINTS):
        return 3
    if any(hint in skill_lower for hint in INTERMEDIATE_HINTS):
        return 2
    # Default: assume intermediate
    return 2


# ============================================================================
# CATEGORY CLASSIFIER
# ============================================================================

def _classify_category(skill: str) -> str:
    """Determine which category a skill belongs to."""
    skill_lower = skill.lower()
    for category, skills_in_cat in CATEGORY_KEYWORDS.items():
        if skill_lower in skills_in_cat:
            return category
    return "general"


# ============================================================================
# PUBLIC API
# ============================================================================

@lru_cache(maxsize=1000)
def classify_skill(skill: str) -> dict:
    """
    Main entry point — classify a skill into tier, weeks, and category.

    Args:
        skill: The skill name (e.g., "python", "kubernetes")

    Returns:
        {
            "skill":     str,
            "tier":      int   (1, 2, or 3),
            "tier_name": str   ("foundation", "intermediate", "advanced"),
            "weeks":     int,
            "category":  str
        }
    """
    skill_lower = skill.lower().strip()

    # Determine tier
    if skill_lower in FOUNDATION_SKILLS:
        tier = 1
    elif skill_lower in INTERMEDIATE_SKILLS:
        tier = 2
    elif skill_lower in ADVANCED_SKILLS:
        tier = 3
    else:
        # Fallback heuristic
        tier = _fallback_tier(skill_lower)

    tier_names = {1: "foundation", 2: "intermediate", 3: "advanced"}

    return {
        "skill": skill_lower,
        "tier": tier,
        "tier_name": tier_names[tier],
        "weeks": TIER_WEEKS[tier],
        "category": _classify_category(skill_lower),
    }


def get_tier_summary() -> dict:
    """Return statistics about the skill tier database."""
    return {
        "foundation_count": len(FOUNDATION_SKILLS),
        "intermediate_count": len(INTERMEDIATE_SKILLS),
        "advanced_count": len(ADVANCED_SKILLS),
        "total_curated": len(FOUNDATION_SKILLS) + len(INTERMEDIATE_SKILLS) + len(ADVANCED_SKILLS),
        "categories": list(CATEGORY_KEYWORDS.keys()),
    }


# ============================================================================
# STANDALONE TEST
# ============================================================================

if __name__ == "__main__":
    """Test classifier on sample skills."""
    print("\n" + "=" * 70)
    print("  SKILL TIER CLASSIFIER — TEST")
    print("=" * 70)

    summary = get_tier_summary()
    print(f"\nCurated skills:")
    print(f"  Foundation:   {summary['foundation_count']}")
    print(f"  Intermediate: {summary['intermediate_count']}")
    print(f"  Advanced:     {summary['advanced_count']}")
    print(f"  Total:        {summary['total_curated']}")
    print(f"  Categories:   {len(summary['categories'])}")

    # Test sample skills
    test_skills = [
        "python", "sql", "git", "html",                        # Foundation
        "react", "flask", "tensorflow", "docker", "aws",       # Intermediate
        "kubernetes", "terraform", "spark", "cissp",           # Advanced
        "communication", "leadership",                          # Soft (foundation)
        "weird_unknown_skill",                                  # Fallback
        "data engineering architecture",                        # Fallback advanced
    ]

    print("\n" + "=" * 70)
    print("  CLASSIFICATIONS")
    print("=" * 70)
    print(f"{'Skill':<30} {'Tier':<15} {'Weeks':<8} {'Category':<15}")
    print("-" * 70)

    for s in test_skills:
        result = classify_skill(s)
        tier_label = f"T{result['tier']} - {result['tier_name']}"
        print(f"{s:<30} {tier_label:<15} {result['weeks']:<8} {result['category']}")

    print("\n" + "=" * 70)