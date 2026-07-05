import os
import joblib
import numpy as np
from functools import lru_cache

"""
Purpose:
    Use the trained Random Forest classifier to PREDICT the user's best-fit
    career role from their extracted skills.
"""

# ============================================================================
# PATH CONFIGURATION
# ============================================================================

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
MODEL_DIR = os.path.join(BASE_DIR, "ml", "saved_models")

TFIDF_PATH         = os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl")
RF_MODEL_PATH      = os.path.join(MODEL_DIR, "rf_career_model.pkl")
KNN_MODEL_PATH     = os.path.join(MODEL_DIR, "knn_readiness_model.pkl")
LABEL_ENCODER_PATH = os.path.join(MODEL_DIR, "label_encoder.pkl")


# ============================================================================
# LAZY-LOADED MODEL CACHE
# ============================================================================
# Models are heavy (RF = 158 MB). Load once, reuse forever.

@lru_cache(maxsize=1)
def get_tfidf_vectorizer():
    """Load the TF-IDF vectorizer."""
    if not os.path.exists(TFIDF_PATH):
        raise FileNotFoundError(
            f"TF-IDF vectorizer not found at {TFIDF_PATH}. "
            f"Run: python ml/training/train_models.py"
        )
    return joblib.load(TFIDF_PATH)


@lru_cache(maxsize=1)
def get_rf_model():
    """Load the Random Forest career classifier."""
    if not os.path.exists(RF_MODEL_PATH):
        raise FileNotFoundError(
            f"Random Forest model not found at {RF_MODEL_PATH}. "
            f"Run: python ml/training/train_models.py"
        )
    return joblib.load(RF_MODEL_PATH)


@lru_cache(maxsize=1)
def get_knn_model():
    """Load the KNN readiness model."""
    if not os.path.exists(KNN_MODEL_PATH):
        raise FileNotFoundError(
            f"KNN model not found at {KNN_MODEL_PATH}."
        )
    return joblib.load(KNN_MODEL_PATH)


@lru_cache(maxsize=1)
def get_label_encoder():
    """Load the label encoder for role names."""
    if not os.path.exists(LABEL_ENCODER_PATH):
        raise FileNotFoundError(
            f"Label encoder not found at {LABEL_ENCODER_PATH}."
        )
    return joblib.load(LABEL_ENCODER_PATH)


# ============================================================================
# HELPERS
# ============================================================================

def _vectorize_user_skills(user_skills: list) -> "np.ndarray":
    """
    Convert a list of user skills into a TF-IDF vector compatible with our models.

    Args:
        user_skills: List of skill strings (e.g., ["python", "sql", "tableau"])

    Returns:
        sparse matrix of shape (1, 5000) — same format the model trained on
    """
    vectorizer = get_tfidf_vectorizer()

    # Join skills into a comma-separated string (same as training data format)
    skills_text = ", ".join(user_skills)

    return vectorizer.transform([skills_text])


def _compute_readiness(user_vector) -> dict:
    """
    Use KNN to find similarity to actual jobs in training data.
    Returns readiness score 0-100.
    """
    knn = get_knn_model()
    distances, _ = knn.kneighbors(user_vector, n_neighbors=5)

    avg_distance = float(np.mean(distances))

    # Calibrated linear scaling (same as gap_analyzer for consistency)
    MIN_DIST = 0.5
    MAX_DIST = 1.4

    if avg_distance <= MIN_DIST:
        similarity = 1.0
    elif avg_distance >= MAX_DIST:
        similarity = 0.0
    else:
        similarity = 1.0 - ((avg_distance - MIN_DIST) / (MAX_DIST - MIN_DIST))

    return {
        "readiness_percentage": round(similarity * 100, 1),
        "avg_distance_to_real_jobs": round(avg_distance, 3),
    }


# ============================================================================
# PUBLIC API
# ============================================================================

def predict_career(user_skills: list, top_k: int = 3) -> dict:
    """
    Predict the user's most likely career role(s) from their skills.

    Args:
        user_skills: List of skill strings
        top_k:       Number of top predictions to return (default 3)

    Returns:
        {
            "user_skills": [...],
            "user_skill_count": int,
            "primary_prediction": {
                "role":       "Data Scientist",
                "confidence": 78.5
            },
            "top_predictions": [
                {"role": "Data Scientist", "confidence": 78.5},
                {"role": "Data Engineer",  "confidence": 12.3},
                {"role": "Data Analyst",   "confidence":  6.2},
                ...
            ],
            "career_readiness": {
                "readiness_percentage": 65.4,
                "avg_distance_to_real_jobs": 0.82
            }
        }
    """
    if not user_skills:
        return {
            "error": "No skills provided. Cannot predict career.",
            "user_skills": [],
        }

    # 1. Normalize skills
    normalized = sorted({s.lower().strip() for s in user_skills if s.strip()})

    if not normalized:
        return {
            "error": "All provided skills are empty after normalization.",
            "user_skills": [],
        }

    # 2. Vectorize user's skill profile (text → TF-IDF vector)
    user_vector = _vectorize_user_skills(normalized)

    # 3. Run Random Forest prediction
    rf_model = get_rf_model()
    encoder = get_label_encoder()

    # Get class probabilities for ALL roles
    probabilities = rf_model.predict_proba(user_vector)[0]

    # Match probabilities to role names
    role_probs = []
    for class_idx, prob in enumerate(probabilities):
        role_name = encoder.inverse_transform([class_idx])[0]
        role_probs.append({
            "role": role_name,
            "confidence": round(float(prob) * 100, 1),
        })

    # Sort by confidence descending
    role_probs.sort(key=lambda x: -x["confidence"])

    # 4. Get top K predictions
    top_k = max(1, min(top_k, len(role_probs)))  # Clamp between 1 and 11
    top_predictions = role_probs[:top_k]

    # 5. Compute readiness via KNN
    readiness = _compute_readiness(user_vector)

    # 6. Build response
    return {
        "user_skills": normalized,
        "user_skill_count": len(normalized),
        "primary_prediction": top_predictions[0],
        "top_predictions": top_predictions,
        "career_readiness": readiness,
        "all_role_confidences": role_probs,  # For frontend chart/visualization
    }


def get_available_roles() -> list:
    """
    Return the list of role categories the model can predict.

    Returns:
        List of role names (e.g., ["Backend Developer", "Cybersecurity Analyst", ...])
    """
    encoder = get_label_encoder()
    return sorted(encoder.classes_.tolist())


# ============================================================================
# STANDALONE TEST
# ============================================================================

if __name__ == "__main__":
    """Test runner: predict careers for sample user profiles."""
    print("\n" + "=" * 76)
    print("  CAREER PREDICTOR — TEST")
    print("=" * 76)

    # List available roles
    roles = get_available_roles()
    print(f"\nAvailable role classes ({len(roles)}):")
    for r in roles:
        print(f"  • {r}")

    # Test profiles
    profiles = [
        {
            "name": "Aspiring Data Scientist",
            "skills": ["python", "machine learning", "sql", "tensorflow",
                       "statistics", "pandas", "deep learning"],
        },
        {
            "name": "Junior Frontend Developer",
            "skills": ["javascript", "html", "css", "react", "git"],
        },
        {
            "name": "Senior DevOps Engineer",
            "skills": ["kubernetes", "terraform", "aws", "docker", "jenkins",
                       "ansible", "linux", "ci/cd", "python", "prometheus"],
        },
        {
            "name": "Diverse Profile (Zayed-like)",
            "skills": ["python", "java", "c++", "html", "css", "react",
                       "mysql", "mongodb", "machine learning", "tensorflow",
                       "computer vision", "data analysis"],
        },
    ]

    for profile in profiles:
        print(f"\n{'═' * 76}")
        print(f"  USER: {profile['name']}")
        print(f"{'═' * 76}")
        print(f"  Skills ({len(profile['skills'])}): {', '.join(profile['skills'])}")

        result = predict_career(profile["skills"], top_k=3)

        if "error" in result:
            print(f"  ⚠️ Error: {result['error']}")
            continue

        primary = result["primary_prediction"]
        readiness = result["career_readiness"]

        print(f"\n  🎯 PRIMARY PREDICTION:")
        print(f"     {primary['role']}  ({primary['confidence']}% confidence)")

        print(f"\n  📊 TOP 3:")
        for i, p in enumerate(result["top_predictions"], 1):
            bar = "█" * int(p["confidence"] / 5)
            print(f"     {i}. {p['role']:<25} {p['confidence']:>5.1f}%  {bar}")

        print(f"\n  💼 CAREER READINESS: {readiness['readiness_percentage']}%")

    print(f"\n{'=' * 76}\n")