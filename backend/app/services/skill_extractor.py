import os
import re
import joblib
import spacy
from functools import lru_cache

"""
Purpose:
    Extract a clean list of professional IT skills from resume text using
    a hybrid 3-layer NLP approach:
"""

# ============================================================================
# CONFIGURATION
# ============================================================================

SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(SERVICE_DIR, "..", ".."))
MODELS_DIR = os.path.join(BACKEND_ROOT, "ml", "saved_models")

SKILL_DB_PATH = os.path.join(MODELS_DIR, "skill_database.pkl")
TFIDF_PATH = os.path.join(MODELS_DIR, "tfidf_vectorizer.pkl")


# ============================================================================
# LAZY-LOADED RESOURCES (singleton via lru_cache)
# ============================================================================
# These resources are loaded ONCE on first call and cached.
# - skill_database.pkl ~ 11 KB
# - tfidf_vectorizer.pkl ~ 207 KB
# - spaCy en_core_web_sm ~ 50 MB

@lru_cache(maxsize=1)
def get_skill_database():
    """Load the master skill database (626 IT skills + aliases)."""
    if not os.path.exists(SKILL_DB_PATH):
        raise FileNotFoundError(
            f"Skill database not found at {SKILL_DB_PATH}. "
            f"Run ml/training/build_skill_db.py first."
        )
    return joblib.load(SKILL_DB_PATH)


@lru_cache(maxsize=1)
def get_tfidf_vectorizer():
    """Load the trained TF-IDF vectorizer."""
    if not os.path.exists(TFIDF_PATH):
        raise FileNotFoundError(
            f"TF-IDF vectorizer not found at {TFIDF_PATH}. "
            f"Run ml/training/train_models.py first."
        )
    return joblib.load(TFIDF_PATH)


@lru_cache(maxsize=1)
def get_spacy_model():
    """Load the spaCy English NER model (slow first load, ~5 seconds)."""
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        raise RuntimeError(
            "spaCy model 'en_core_web_sm' is not installed. "
            "Run: python -m spacy download en_core_web_sm"
        )


# ============================================================================
# TEXT NORMALIZATION
# ============================================================================

def normalize_text(text: str) -> str:
    """Normalize for matching: lowercase + collapse whitespace."""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text


# ============================================================================
# LAYER 1 — DICTIONARY MATCHING
# ============================================================================

def layer_1_dictionary_match(text: str, skill_db: dict) -> set:
    """
    Find all skills from the canonical skill database in the resume text.

    Uses regex word-boundary matching so 'java' doesn't match 'javascript'
    and 'r' doesn't match 'reader'.

    Args:
        text:     Normalized resume text
        skill_db: Loaded skill database dict

    Returns:
        Set of canonical skill strings found in the text
    """
    text_norm = " " + normalize_text(text) + " "
    canonical_skills = skill_db["canonical_skills"]
    alias_map = skill_db["alias_map"]

    found = set()

    # Build search pairs: (search_term, canonical_form)
    search_pairs = [(skill, skill) for skill in canonical_skills]
    for alias, canonical in alias_map.items():
        if canonical in canonical_skills:
            search_pairs.append((alias, canonical))

    # Sort by length desc — match longer skills first
    # (so "machine learning" beats "machine")
    search_pairs.sort(key=lambda x: -len(x[0]))

    for search_term, canonical in search_pairs:
        # Escape special regex chars in skill (e.g., '+', '#', '.', '/')
        escaped = re.escape(search_term)
        # Custom boundary: no letter/digit on either side
        # This handles c++ , c#, .net, node.js, ci/cd correctly
        pattern = rf"(?<![a-zA-Z0-9]){escaped}(?![a-zA-Z0-9])"

        if re.search(pattern, text_norm):
            found.add(canonical)

    return found


# ============================================================================
# LAYER 2 — spaCy NAMED ENTITY RECOGNITION
# ============================================================================

# spaCy entity labels that often correspond to tech/skills
TECH_ENTITY_LABELS = {"ORG", "PRODUCT", "WORK_OF_ART", "LANGUAGE"}


# ============================================================================
# FILTERS — Words that look like skills but aren't
# ============================================================================

# Section headers and overly generic words from skill database that pollute output
GENERIC_FILTER = {
    "programming", "databases", "software", "design",
    "tools", "languages", "skills", "technologies",
    "computer science", "training", "reporting",
    "computer", "general", "engineering",
    "development", "computing", "data", "systems",
    "applications", "platforms", "services", # Too generic — fields/concepts, not learnable skills
"ai",
"algorithms",
"algorithm",
"api",                # redundant when "api integration" exists
"analytics",
"technology",
"technologies",
"system",
"systems",
"tools",
"methodology",
"concepts",
"techniques",
}

# Common English words that match ALL-CAPS pattern but aren't tech
COMMON_CAPS_WORDS = {
    "PROFILE", "SKILLS", "EDUCATION", "CONTACT", "RESUME", "CV",
    "PROJECT", "PROJECTS", "EXPERIENCE", "SUMMARY", "OBJECTIVE",
    "REFERENCES", "LANGUAGES", "HOBBIES", "INTERESTS",
    "CERTIFICATES", "CERTIFICATIONS", "ACHIEVEMENTS",
    "CGPA", "GPA", "PHD", "BS", "MS", "BA", "MA",
    "EMAIL", "PHONE", "LINKEDIN", "GITHUB", "WEBSITE",
    "AND", "OR", "THE", "FOR", "WITH", "USING", "FROM",
    "PRESENT", "CURRENT", "PAST", "FUTURE", "NEW",
    "PDF", "DOC", "DOCX", "HTML", "URL",  # file types (HTML handled separately)
    "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
    "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
}

# Known tech acronyms — whitelist for ALL CAPS to ensure they're captured
# (in case dictionary missed them as standalone)
TECH_CAPS_WHITELIST = {
    "AWS", "GCP", "AI", "ML", "NLP", "API", "SDK", "CLI",
    "SQL", "ETL", "CRM", "ERP", "JWT", "OAuth",
    "REST", "GRPC", "GRAPHQL", "WSGI", "ASGI",
    "DOM", "AJAX", "CORS", "CDN", "DNS", "TCP", "UDP", "HTTP", "HTTPS",
    "OWASP", "SIEM", "SOC", "VPN", "DDoS",
    "YOLO", "GAN", "RNN", "CNN", "LSTM", "BERT", "GPT", "LLM", "RAG",
    "TPU", "GPU", "CPU", "RAM", "OS",
    "CICD", "DEVOPS", "SRE", "QA",
    "IDE", "VS", "JIRA",
}

def layer_2_spacy_ner(text: str, skill_db: dict) -> set:
    """
    Run spaCy NER on the resume. For each detected entity that looks like
    a tech product/org/language, check if it matches our skill database.

    This catches multi-word entities that the dictionary may have missed
    due to spelling variations.
    """
    nlp = get_spacy_model()
    canonical_skills = skill_db["canonical_skills"]
    alias_map = skill_db["alias_map"]

    # spaCy can be slow on huge docs — truncate at 50K chars
    doc = nlp(text[:50000])

    found = set()
    for ent in doc.ents:
        if ent.label_ not in TECH_ENTITY_LABELS:
            continue

        candidate = ent.text.lower().strip()

        # Direct match
        if candidate in canonical_skills:
            found.add(candidate)
            continue

        # Match via alias map
        normalized = alias_map.get(candidate)
        if normalized and normalized in canonical_skills:
            found.add(normalized)

    return found


# ============================================================================
# LAYER 3 — TF-IDF VOCABULARY MATCHING
# ============================================================================

def layer_3_tfidf_vocab_match(text: str, skill_db: dict) -> set:
    """
    Match resume text against the TF-IDF vectorizer's learned vocabulary.

    This catches domain-specific terms that appeared in our LinkedIn training
    data but might be missed by the smaller curated skill_database.
    """
    vectorizer = get_tfidf_vectorizer()
    canonical_skills = skill_db["canonical_skills"]
    alias_map = skill_db["alias_map"]

    vocab = vectorizer.vocabulary_   # dict: term → feature index
    text_norm = " " + normalize_text(text) + " "

    found = set()
    for term in vocab.keys():
        escaped = re.escape(term)
        pattern = rf"(?<![a-zA-Z0-9]){escaped}(?![a-zA-Z0-9])"

        if re.search(pattern, text_norm):
            # Only keep it if it maps to a real canonical skill
            normalized = alias_map.get(term, term)
            if normalized in canonical_skills:
                found.add(normalized)

    return found


# ============================================================================
# LAYER 4 — PATTERN-BASED DISCOVERY (NEW IN B+ LITE)
# ============================================================================

def layer_4_pattern_detection(text: str, skill_db: dict) -> set:
    """
    Discover new skills using regex patterns common in tech naming.

    This catches skills NOT in our dictionary — like new frameworks,
    libraries, and tools. Works on any resume without manual database
    updates.

    Patterns detected:
      Pattern A — ALL CAPS acronyms (3-6 chars): YOLO, LLM, AWS
      Pattern B — CamelCase tech terms: OpenCV, MongoDB, TensorFlow
      Pattern C — Dotted tech names: Node.js, Vue.js, Express.js

    Args:
        text:     Raw resume text (preserves casing — crucial here!)
        skill_db: Loaded skill database (for cross-checking)

    Returns:
        Set of discovered skill strings (lowercased canonical form)
    """
    canonical_skills = skill_db["canonical_skills"]
    alias_map = skill_db["alias_map"]

    discovered = set()

    # ────────────────────────────────────────────────────────────────────
    # Pattern A — ALL CAPS acronyms (3 to 6 chars)
    # Catches: YOLO, LLM, AWS, SQL, REST, NLP, OWASP
    # ────────────────────────────────────────────────────────────────────
    all_caps_matches = re.findall(r'\b[A-Z]{3,6}\b', text)
    for term in all_caps_matches:
        # Skip common English/non-tech words
        if term in COMMON_CAPS_WORDS:
            continue
        # Skip very short or numeric-only
        if len(term) < 3 or term.isdigit():
            continue

        canonical = term.lower()

        # Apply alias mapping
        canonical = alias_map.get(canonical, canonical)

        # Add if: (a) already in dictionary, OR (b) in tech whitelist
        if canonical in canonical_skills:
            discovered.add(canonical)
        elif term in TECH_CAPS_WHITELIST:
            discovered.add(canonical)

    # ────────────────────────────────────────────────────────────────────
    # Pattern B — CamelCase tech terms (e.g., OpenCV, MongoDB)
    # Must have: starting capital + lowercase + another capital + more chars
    # Catches: OpenCV, MongoDB, JavaScript, TypeScript, TensorFlow, PyTorch,
    #          MiniLM, OpenAI, GitHub, JavaFX, MySQL, NodeJS
    # ────────────────────────────────────────────────────────────────────
    camel_matches = re.findall(r'\b[A-Z][a-z]+[A-Z][A-Za-z0-9]+\b', text)
    for term in camel_matches:
        canonical = term.lower()
        # Apply alias mapping
        canonical = alias_map.get(canonical, canonical)
        # Add it — CamelCase is almost always a tech name
        discovered.add(canonical)

    # ────────────────────────────────────────────────────────────────────
    # Pattern C — Dotted tech names (Node.js, Vue.js, Next.js)
    # ────────────────────────────────────────────────────────────────────
    dotted_matches = re.findall(r'\b[A-Za-z][A-Za-z0-9]*\.(?:js|net|io|ai|py)\b', text)
    for term in dotted_matches:
        canonical = term.lower()
        canonical = alias_map.get(canonical, canonical)
        discovered.add(canonical)

    return discovered


# ============================================================================
# PUBLIC API
# ============================================================================

def extract_skills(text: str) -> dict:
    """
    Main entry point — extract skills from resume text using the 3-layer
    hybrid NLP approach.

    Args:
        text: Clean resume text (output of resume_parser.parse_resume()).

    Returns:
        {
            "skills":      [sorted list of canonical skill strings],
            "skill_count": int,
            "extraction_details": {
                "layer_1_matches": int,
                "layer_2_matches": int,
                "layer_3_matches": int,
                "union_size":      int,
            },
            "layer_breakdown": {
                "dictionary_only": [...],   # found by Layer 1 only
                "spacy_only":      [...],   # found by Layer 2 only
                "tfidf_only":      [...],   # found by Layer 3 only
                "common_to_all":   [...],   # found by all 3 layers
            }
        }
    """
    # Safety guard
    if not text or len(text.strip()) < 20:
        return {
            "skills": [],
            "skill_count": 0,
            "extraction_details": {
                "layer_1_matches": 0,
                "layer_2_matches": 0,
                "layer_3_matches": 0,
                "union_size": 0,
            },
            "error": "Text too short to analyze",
        }

    # Load skill database (cached)
    skill_db = get_skill_database()

    # Run all 4 layers
    layer_1 = layer_1_dictionary_match(text, skill_db)
    layer_2 = layer_2_spacy_ner(text, skill_db)
    layer_3 = layer_3_tfidf_vocab_match(text, skill_db)
    layer_4 = layer_4_pattern_detection(text, skill_db)  # ← NEW

    # Union all 4 layers
    all_skills = layer_1 | layer_2 | layer_3 | layer_4

    # Apply generic word filter to remove section headers / noise
    all_skills = all_skills - GENERIC_FILTER


    return {
        "skills": sorted(all_skills),
        "skill_count": len(all_skills),
        "extraction_details": {
            "layer_1_matches": len(layer_1),
            "layer_2_matches": len(layer_2),
            "layer_3_matches": len(layer_3),
            "layer_4_matches": len(layer_4),
            "union_size": len(all_skills),
        },
        "layer_breakdown": {
            "dictionary_only": sorted((layer_1 - layer_2 - layer_3 - layer_4) - GENERIC_FILTER),
            "spacy_only":      sorted((layer_2 - layer_1 - layer_3 - layer_4) - GENERIC_FILTER),
            "tfidf_only":      sorted((layer_3 - layer_1 - layer_2 - layer_4) - GENERIC_FILTER),
            "pattern_only":    sorted((layer_4 - layer_1 - layer_2 - layer_3) - GENERIC_FILTER),
            "common_to_known": sorted((layer_1 & layer_2 & layer_3) - GENERIC_FILTER),
        },
    }


# ============================================================================
# STANDALONE TEST RUNNER
# ============================================================================

if __name__ == "__main__":
    """
    Test runner: extract skills from a resume file (PDF or DOCX).

    Usage:
        python -m app.services.skill_extractor <path_to_resume>
    """
    import sys
    from .resume_parser import parse_resume

    if len(sys.argv) < 2:
        print("Usage: python -m app.services.skill_extractor <path_to_resume>")
        sys.exit(1)

    file_path = sys.argv[1]

    print("\n" + "=" * 78)
    print("  SKILL EXTRACTOR — TEST RESULT")
    print("=" * 78)
    print(f"Input file: {file_path}")

    # Stage 1 — parse resume
    print("\n[1/2] Parsing resume...")
    parse_result = parse_resume(file_path)
    if not parse_result["success"]:
        print(f"✗ Resume parsing failed: {parse_result['error']}")
        sys.exit(1)
    print(f"✓ Parsed: {parse_result['word_count']} words, {parse_result['char_count']} chars")

    # Stage 2 — extract skills
    print("\n[2/2] Extracting skills (first run loads spaCy ~10s)...")
    result = extract_skills(parse_result["text"])

    # Display results
    print(f"\n  ✓ Total unique skills found: {result['skill_count']}")

    print(f"\n  Layer breakdown (matches per layer, may overlap):")
    print(f"    Layer 1 — Dictionary:        {result['extraction_details']['layer_1_matches']} matches")
    print(f"    Layer 2 — spaCy NER:         {result['extraction_details']['layer_2_matches']} matches")
    print(f"    Layer 3 — TF-IDF vocab:      {result['extraction_details']['layer_3_matches']} matches")
    print(f"    Layer 4 — Pattern detection: {result['extraction_details']['layer_4_matches']} matches  🆕")

    print(f"\n   Extracted Skills (final union):")
    for i, skill in enumerate(result["skills"], 1):
        print(f"    {i:>2}. {skill}")

    print(f"\n   Where each skill was found:")
    bd = result["layer_breakdown"]

    if bd.get("common_to_known"):
        print(f"\n    Found by ALL 3 known-skill layers (highest confidence):")
        for s in bd["common_to_known"]:
            print(f"      ✓✓✓ {s}")

    if bd["dictionary_only"]:
        print(f"\n    Found by DICTIONARY only:")
        for s in bd["dictionary_only"]:
            print(f"        {s}")

    if bd["spacy_only"]:
        print(f"\n    Found by spaCy NER only:")
        for s in bd["spacy_only"]:
            print(f"        {s}")

    if bd["tfidf_only"]:
        print(f"\n    Found by TF-IDF only:")
        for s in bd["tfidf_only"]:
            print(f"        {s}")

    if bd.get("pattern_only"):
        print(f"\n    Found by Pattern Detection only (NEW SKILLS!):")
        for s in bd["pattern_only"]:
            print(f"      🆕  {s}")

    print("\n" + "=" * 78)