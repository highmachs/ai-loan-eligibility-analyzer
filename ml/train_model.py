"""
Phase 2 ML Model Training Script — Intelligent Loan Eligibility Analyzer

Trains a RandomForestClassifier on synthetic banking data with realistic cohort distributions.
Saves:
  - model.pkl        : trained classifier
  - feature_cols.pkl : ordered feature column list for inference
  - dataset.csv      : generated training dataset
"""

import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

FEATURE_COLUMNS = [
    "age",
    "monthly_salary",
    "credit_score",
    "existing_emi",
    "requested_amount",
    "tenure_months",
    "missed_payments",
    "foir",
]

def train_and_save_model() -> str:
    np.random.seed(42)
    N = 3000

    # Cohort 1: Prime (35%)
    N1 = int(N * 0.35)
    c1 = {
        "age": np.random.randint(25, 60, N1),
        "monthly_salary": np.random.randint(60000, 250000, N1),
        "credit_score": np.random.randint(750, 850, N1),
        "existing_emi": np.random.randint(0, 25000, N1),
        "requested_amount": np.random.randint(200000, 2000000, N1),
        "tenure_months": np.random.choice([24, 36, 48, 60, 84], N1),
        "missed_payments": np.zeros(N1, dtype=int),
    }

    # Cohort 2: Moderate (35%)
    N2 = int(N * 0.35)
    c2 = {
        "age": np.random.randint(22, 60, N2),
        "monthly_salary": np.random.randint(35000, 150000, N2),
        "credit_score": np.random.randint(650, 750, N2),
        "existing_emi": np.random.randint(5000, 40000, N2),
        "requested_amount": np.random.randint(500000, 3000000, N2),
        "tenure_months": np.random.choice([36, 48, 60, 84, 120], N2),
        "missed_payments": np.random.choice([0, 1], p=[0.7, 0.3], size=N2),
    }

    # Cohort 3: Subprime / High Risk (30%)
    N3 = N - N1 - N2
    c3 = {
        "age": np.random.randint(21, 60, N3),
        "monthly_salary": np.random.randint(15000, 80000, N3),
        "credit_score": np.random.randint(300, 650, N3),
        "existing_emi": np.random.randint(15000, 60000, N3),
        "requested_amount": np.random.randint(500000, 5000000, N3),
        "tenure_months": np.random.choice([12, 24, 36, 60], N3),
        "missed_payments": np.random.randint(1, 6, N3),
    }

    dfs = [pd.DataFrame(c1), pd.DataFrame(c2), pd.DataFrame(c3)]
    df = pd.concat(dfs, ignore_index=True)
    df["proposed_emi"] = df["requested_amount"] / df["tenure_months"]
    df["foir"] = (df["existing_emi"] + df["proposed_emi"]) / df["monthly_salary"] * 100

    df["approved"] = (
        (df["credit_score"] >= 650)
        & (df["foir"] <= 55)
        & (df["missed_payments"] == 0)
    ).astype(int)

    ml_dir = os.path.dirname(__file__)
    df.to_csv(os.path.join(ml_dir, "dataset.csv"), index=False)

    X = df[FEATURE_COLUMNS]
    y = df["approved"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        random_state=42,
    )
    model.fit(X_train, y_train)

    joblib.dump(model, os.path.join(ml_dir, "model.pkl"))
    joblib.dump(FEATURE_COLUMNS, os.path.join(ml_dir, "feature_cols.pkl"))

    return f"Dataset saved: {len(df)} rows. Model accuracy: {accuracy_score(y_test, model.predict(X_test)):.4f}"

if __name__ == "__main__":
    msg = train_and_save_model()
    print(msg)
    print("Phase 2 ML model ready for backend integration.")
