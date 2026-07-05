
import os
import sys
import joblib
from datetime import datetime

import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

"""
Purpose:
    Train and evaluate all ML models for the AI Career Navigator system.
"""

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

INPUT_FILE = os.path.join(PROJECT_ROOT, "data", "processed", "cleaned_jobs.csv")
MODELS_DIR = os.path.join(PROJECT_ROOT, "ml", "saved_models")
REPORT_FILE = os.path.join(PROJECT_ROOT, "data", "processed", "model_evaluation_report.txt")

# Reproducibility seed — same value every run
RANDOM_STATE = 42

# Hyperparameters (matching FYP Chapter 2 specification)
TFIDF_MAX_FEATURES = 5000
TFIDF_NGRAM_RANGE = (1, 2)

RF_N_ESTIMATORS = 100
RF_CRITERION = "gini"

KNN_K = 5
KNN_METRIC = "euclidean"

TEST_SIZE = 0.20

# Accumulator for the evaluation report
report_log = []


# ============================================================================
# UTILITIES
# ============================================================================

def log(msg=""):
    """Print to terminal and accumulate for report file."""
    print(msg)
    report_log.append(msg)


def section(title):
    sep = "=" * 78
    log(f"\n{sep}")
    log(f"  {title}")
    log(sep)


# ============================================================================
# STAGE 1 — LOAD CLEANED DATA
# ============================================================================

def load_data():
    section("STAGE 1 — LOAD CLEANED JOBS DATASET")

    if not os.path.exists(INPUT_FILE):
        log(f"❌ ERROR: {INPUT_FILE} not found.")
        log("   Run preprocess_data.py first.")
        sys.exit(1)

    df = pd.read_csv(INPUT_FILE)
    log(f"✓ Loaded {len(df):,} rows from {os.path.basename(INPUT_FILE)}")
    log(f"  Columns: {list(df.columns)}")

    # Drop any null skills as a safety net
    df = df.dropna(subset=["job_skills", "role_category", "job_level"])
    log(f"  After dropping nulls: {len(df):,} rows")

    log("\nClass distribution — role_category:")
    for role, count in df["role_category"].value_counts().items():
        pct = count / len(df) * 100
        log(f"  {role:<25} {count:>6,}  ({pct:5.1f}%)")

    log("\nClass distribution — job_level:")
    for level, count in df["job_level"].value_counts().items():
        pct = count / len(df) * 100
        log(f"  {level:<10} {count:>6,}  ({pct:5.1f}%)")

    return df


# ============================================================================
# STAGE 2 — TRAIN TF-IDF VECTORIZER
# ============================================================================

def train_tfidf(df):
    """
    Convert the comma-separated skill text into TF-IDF numerical vectors.

    Why TF-IDF instead of CountVectorizer:
      - Down-weights skills that appear in almost every job (e.g. "communication")
      - Up-weights rare, specialized skills (e.g. "kubernetes")
      - This produces more discriminative features for classification
    """
    section("STAGE 2 — TRAIN TF-IDF VECTORIZER")

    log(f"Configuration (matching FYP Chapter 2):")
    log(f"  max_features = {TFIDF_MAX_FEATURES}")
    log(f"  ngram_range  = {TFIDF_NGRAM_RANGE}  (captures multi-word skills)")
    log(f"  lowercase    = True")
    log(f"  stop_words   = 'english'")

    vectorizer = TfidfVectorizer(
        max_features=TFIDF_MAX_FEATURES,
        ngram_range=TFIDF_NGRAM_RANGE,
        lowercase=True,
        stop_words="english",
        token_pattern=r"[a-zA-Z][a-zA-Z0-9+#.\-/]*",  # supports c++, c#, node.js, ci/cd
    )

    log("\nFitting TF-IDF on the job_skills column...")
    X = vectorizer.fit_transform(df["job_skills"])

    log(f"✓ TF-IDF matrix shape: {X.shape}")
    log(f"  Rows (jobs):    {X.shape[0]:,}")
    log(f"  Cols (features): {X.shape[1]:,}")
    log(f"  Sparsity: {(1 - X.nnz / (X.shape[0] * X.shape[1])) * 100:.2f}% (typical for text)")

    return vectorizer, X


# ============================================================================
# STAGE 3 — TRAIN RANDOM FOREST (CAREER ROLE PREDICTION)
# ============================================================================

def train_random_forest(X, y_role):
    """
    Train a Random Forest classifier to predict role_category from skills.

    Why class_weight='balanced':
      Software Engineer has 12,427 rows but Frontend Developer has only 418.
      Without weighting, the model would bias toward predicting Software Engineer.
      'balanced' inversely weights classes so the model treats them equitably.
    """
    section("STAGE 3 — TRAIN RANDOM FOREST (CAREER ROLE PREDICTION)")

    # Encode role_category as integer labels
    log("Encoding role names to integer labels...")
    encoder = LabelEncoder()
    y_encoded = encoder.fit_transform(y_role)
    log(f"  {len(encoder.classes_)} unique classes:")
    for idx, name in enumerate(encoder.classes_):
        log(f"    {idx:>2} → {name}")

    # 80/20 stratified train-test split
    log(f"\nSplitting 80% train / 20% test (stratified, seed={RANDOM_STATE})...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y_encoded,
    )
    log(f"  Train: {X_train.shape[0]:,} rows")
    log(f"  Test:  {X_test.shape[0]:,} rows")

    # Train the model
    log(f"\nTraining RandomForestClassifier:")
    log(f"  n_estimators = {RF_N_ESTIMATORS}")
    log(f"  criterion    = '{RF_CRITERION}'")
    log(f"  class_weight = 'balanced'")
    log(f"  n_jobs       = -1  (use all CPU cores)")

    rf = RandomForestClassifier(
        n_estimators=RF_N_ESTIMATORS,
        criterion=RF_CRITERION,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    log("\nFitting... (this may take 1-2 minutes)")
    start = datetime.now()
    rf.fit(X_train, y_train)
    elapsed = (datetime.now() - start).total_seconds()
    log(f"✓ Trained in {elapsed:.1f} seconds")

    # Evaluate
    log("\nEvaluating on test set...")
    y_pred = rf.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average="macro", zero_division=0)
    f1_weighted = f1_score(y_test, y_pred, average="weighted", zero_division=0)

    log(f"\n  Accuracy:        {acc:.4f}  ({acc*100:.2f}%)")
    log(f"  F1 (macro):      {f1_macro:.4f}  ← primary metric for imbalanced data")
    log(f"  F1 (weighted):   {f1_weighted:.4f}")

    log("\nPer-class classification report:")
    log(classification_report(
        y_test, y_pred,
        target_names=encoder.classes_,
        zero_division=0,
    ))

    log("Confusion Matrix (rows = true, columns = predicted):")
    cm = confusion_matrix(y_test, y_pred)
    header = "        " + " ".join(f"{i:>5}" for i in range(len(encoder.classes_)))
    log(header)
    for i, row in enumerate(cm):
        row_str = " ".join(f"{v:>5}" for v in row)
        log(f"  {i:>2} -> {row_str}  ({encoder.classes_[i]})")

    return rf, encoder


# ============================================================================
# STAGE 4 — TRAIN KNN (CAREER READINESS / JOB LEVEL)
# ============================================================================

def train_knn(X, y_level):
    """
    Train a K-Nearest Neighbors classifier to predict job_level.

    Why KNN:
      Level prediction is essentially a similarity task: "Which level's skill
      profile does this user resemble most?" KNN does this naturally by
      finding the K most similar training examples and majority-voting.
    """
    section("STAGE 4 — TRAIN KNN (CAREER READINESS / JOB LEVEL)")

    # KNN does not need LabelEncoder strictly, but we'll use sklearn's
    # native handling of string labels for cleaner output.
    log("Job level classes:")
    levels = sorted(y_level.unique().tolist())
    for lvl in levels:
        count = (y_level == lvl).sum()
        log(f"  {lvl:<10} {count:>6,}")

    # 80/20 stratified split
    log(f"\nSplitting 80% train / 20% test (stratified, seed={RANDOM_STATE})...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_level,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y_level,
    )
    log(f"  Train: {X_train.shape[0]:,} rows")
    log(f"  Test:  {X_test.shape[0]:,} rows")

    # Train the model
    log(f"\nTraining KNeighborsClassifier:")
    log(f"  n_neighbors = {KNN_K}")
    log(f"  metric      = '{KNN_METRIC}'")
    log(f"  n_jobs      = -1")

    knn = KNeighborsClassifier(
        n_neighbors=KNN_K,
        metric=KNN_METRIC,
        n_jobs=-1,
    )

    log("\nFitting... (KNN training is fast — it just memorizes)")
    start = datetime.now()
    knn.fit(X_train, y_train)
    elapsed = (datetime.now() - start).total_seconds()
    log(f"✓ Trained in {elapsed:.1f} seconds")

    # Evaluate
    log("\nEvaluating on test set... (KNN prediction is slow — be patient)")
    y_pred = knn.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average="macro", zero_division=0)
    f1_weighted = f1_score(y_test, y_pred, average="weighted", zero_division=0)

    log(f"\n  Accuracy:        {acc:.4f}  ({acc*100:.2f}%)")
    log(f"  F1 (macro):      {f1_macro:.4f}")
    log(f"  F1 (weighted):   {f1_weighted:.4f}")

    log("\nPer-class classification report:")
    log(classification_report(y_test, y_pred, zero_division=0))

    log("Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred, labels=levels)
    log(f"        {' '.join(f'{l:>7}' for l in levels)}")
    for i, lvl in enumerate(levels):
        row_str = " ".join(f"{v:>7}" for v in cm[i])
        log(f"  {lvl:<6}{row_str}")

    return knn


# ============================================================================
# STAGE 5 — SAVE ALL ARTIFACTS
# ============================================================================

def save_models(vectorizer, rf, encoder, knn):
    section("STAGE 5 — SAVE TRAINED MODELS")

    os.makedirs(MODELS_DIR, exist_ok=True)

    artifacts = {
        "tfidf_vectorizer.pkl": vectorizer,
        "rf_career_model.pkl": rf,
        "label_encoder.pkl": encoder,
        "knn_readiness_model.pkl": knn,
    }

    for filename, obj in artifacts.items():
        path = os.path.join(MODELS_DIR, filename)
        joblib.dump(obj, path)
        size_kb = os.path.getsize(path) / 1024
        log(f"✓ Saved {filename:<30} ({size_kb:>8,.1f} KB)")


# ============================================================================
# STAGE 6 — QUICK SANITY-CHECK PREDICTION
# ============================================================================

def sanity_check(vectorizer, rf, encoder, knn):
    """Run a fake user's skills through the trained pipeline."""
    section("STAGE 6 — SANITY CHECK (FAKE USER PREDICTION)")

    fake_users = [
        ("Aspiring Data Scientist",
         "python, machine learning, sql, tensorflow, statistics, pandas, deep learning"),
        ("Junior Frontend Developer",
         "javascript, html, css, react, git"),
        ("Senior DevOps Engineer",
         "kubernetes, terraform, aws, docker, jenkins, ansible, linux, ci/cd, python, prometheus"),
        ("QA Tester",
         "selenium, python, test automation, jira, agile"),
    ]

    for label, skills in fake_users:
        log(f"\nUser: {label}")
        log(f"  Skills: {skills}")

        X_user = vectorizer.transform([skills])

        # Career role prediction
        role_idx = rf.predict(X_user)[0]
        role_name = encoder.classes_[role_idx]

        # Top-3 role probabilities
        proba = rf.predict_proba(X_user)[0]
        top3_idx = np.argsort(proba)[-3:][::-1]

        # Level prediction
        level = knn.predict(X_user)[0]

        log(f"  → Predicted Role:  {role_name}")
        log(f"  → Top 3 matches:")
        for idx in top3_idx:
            log(f"       {encoder.classes_[idx]:<25} {proba[idx]*100:.1f}%")
        log(f"  → Predicted Level: {level}")


# ============================================================================
# REPORT WRITER
# ============================================================================

def write_report():
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    header = (
        "AI Career Navigator — Model Training & Evaluation Report\n"
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Student: Zayed Khaled (B032310764) | UTeM FAIX\n"
        + "=" * 78 + "\n"
    )
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(report_log))
    print(f"\n📄 Report saved: {REPORT_FILE}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "=" * 78)
    print("  AI CAREER NAVIGATOR — ML MODEL TRAINING PIPELINE")
    print("=" * 78)

    start_time = datetime.now()

    df = load_data()
    vectorizer, X = train_tfidf(df)
    rf, encoder = train_random_forest(X, df["role_category"])
    knn = train_knn(X, df["job_level"])
    save_models(vectorizer, rf, encoder, knn)
    sanity_check(vectorizer, rf, encoder, knn)

    elapsed = (datetime.now() - start_time).total_seconds()
    section("TRAINING COMPLETE")
    log(f"Total time:    {elapsed:.1f} seconds")
    log(f"Models saved:  {MODELS_DIR}")
    log(f"Next phase:    Resume parsing + Flask API integration")

    write_report()


if __name__ == "__main__":
    main()