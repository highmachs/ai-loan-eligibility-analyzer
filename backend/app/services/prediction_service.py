"""
Phase 2 Prediction Service — Intelligent Loan Eligibility Analyzer

Priority: ML model (model.pkl) when available.
Fallback:  Phase 1 rule-based engine if model not loaded.
SHAP:      Feature contribution explanations generated per prediction.
"""

import os
import math
from decimal import Decimal
from typing import Tuple, List

from app.models.customer import Customer, EmploymentType
from app.models.loan_application import LoanApplication

# ── ML model loading ─────────────────────────────────────────────────────────
_model = None
_feature_cols: List[str] = []
_shap_explainer = None

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "model.pkl")
_FEATURE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "feature_cols.pkl")

def _load_model():
    global _model, _feature_cols, _shap_explainer
    try:
        import joblib
        import shap
        _model = joblib.load(os.path.abspath(_MODEL_PATH))
        _feature_cols = joblib.load(os.path.abspath(_FEATURE_PATH))
        _shap_explainer = shap.TreeExplainer(_model)
        print("[PredictionService] ML model loaded successfully.")
    except Exception as e:
        print(f"[PredictionService] ML model unavailable, using rule engine. Reason: {e}")
        _model = None

_load_model()


# ── Shared helpers ────────────────────────────────────────────────────────────

def calculate_foir(
    existing_emi: Decimal,
    requested_amount: Decimal,
    tenure_months: int,
    monthly_salary: Decimal,
) -> Decimal:
    if monthly_salary <= 0 or tenure_months <= 0:
        return Decimal("100")
    proposed_emi = requested_amount / tenure_months
    return round(((existing_emi + proposed_emi) / monthly_salary) * 100, 2)


def get_foir_cap(employment_type: EmploymentType) -> Decimal:
    return Decimal("50") if employment_type == EmploymentType.SALARIED else Decimal("60")


def calculate_recommended_amount(customer: Customer, tenure_months: int) -> Decimal:
    if tenure_months <= 0:
        return Decimal("0")
    foir_cap = get_foir_cap(customer.employment_type)
    max_monthly = (foir_cap / 100) * Decimal(str(customer.monthly_salary)) - Decimal(str(customer.existing_emi))
    if max_monthly <= 0:
        return Decimal("0")
    return round(max_monthly * tenure_months, 2)


# ── ML inference with SHAP explanations ──────────────────────────────────────

def _ml_evaluate(
    customer: Customer,
    application: LoanApplication,
    foir: Decimal,
) -> Tuple[str, Decimal, str]:
    """Run ML model and return (risk_level, approval_probability, reason_string)."""
    import pandas as pd

    row = {
        "age": customer.age,
        "monthly_salary": float(customer.monthly_salary),
        "credit_score": customer.credit_score,
        "existing_emi": float(customer.existing_emi),
        "requested_amount": float(application.requested_amount),
        "tenure_months": application.tenure_months,
        "missed_payments": customer.missed_payments,
        "foir": float(foir),
    }

    X = pd.DataFrame([row])[_feature_cols]
    prob_approved = float(_model.predict_proba(X)[0][1])
    approval_probability = Decimal(str(round(prob_approved * 100, 2)))

    # Risk tier from probability
    if prob_approved >= 0.80:
        risk_level = "LOW"
    elif prob_approved >= 0.50:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    # SHAP explanations
    try:
        import numpy as np
        shap_values = _shap_explainer.shap_values(X)
        if isinstance(shap_values, list):
            sv = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
        elif isinstance(shap_values, np.ndarray):
            if shap_values.ndim == 3:  # (n_samples, n_features, n_classes)
                sv = shap_values[0, :, 1]
            elif shap_values.ndim == 2:  # (n_samples, n_features)
                sv = shap_values[0]
            else:
                sv = shap_values
        else:
            sv = shap_values[0]

        feature_impact = sorted(
            zip(_feature_cols, sv),
            key=lambda x: abs(float(x[1])),
            reverse=True,
        )

        reason_parts = []
        labels = {
            "credit_score": "Credit score",
            "monthly_salary": "Monthly salary",
            "foir": "Debt-to-income ratio",
            "existing_emi": "Existing EMI",
            "missed_payments": "Payment history",
            "requested_amount": "Requested amount",
            "tenure_months": "Loan tenure",
            "age": "Applicant age",
        }
        for feat, raw_impact in feature_impact[:4]:
            impact = float(raw_impact)
            label = labels.get(feat, feat)
            direction = "increased" if impact > 0 else "reduced"
            pct = abs(round(impact * 100, 1))
            if pct > 0:
                reason_parts.append(f"{label} {direction} approval chance by {pct}%")

        reason = "; ".join(reason_parts) if reason_parts else "ML model evaluation complete"
    except Exception as e:
        # Graceful fallback if SHAP fails
        print(f"[PredictionService] SHAP extraction error: {e}")
        reason = _rule_reasons(customer, foir, get_foir_cap(customer.employment_type))

    return risk_level, approval_probability, reason


# ── Rule-based fallback ───────────────────────────────────────────────────────

def _rule_reasons(customer: Customer, foir: Decimal, foir_cap: Decimal) -> str:
    reasons = []
    if customer.credit_score > 750:
        reasons.append("Excellent credit score")
    elif customer.credit_score >= 650:
        reasons.append("Moderate credit score")
    else:
        reasons.append("Poor credit score")

    reasons.append("Low debt burden" if foir <= foir_cap else "High debt burden")

    if customer.monthly_salary > 0:
        reasons.append("Good salary")

    reasons.append("No defaults" if customer.missed_payments == 0 else "Previous missed payments")
    return ", ".join(reasons)


def _rule_evaluate(
    customer: Customer,
    foir: Decimal,
    foir_cap: Decimal,
    missed_payments: int,
) -> Tuple[str, Decimal]:
    credit_score = customer.credit_score
    if credit_score > 750 and foir < foir_cap and missed_payments == 0:
        return "LOW", Decimal("92")
    elif credit_score >= 650 and foir <= foir_cap:
        return "MEDIUM", Decimal("65")
    else:
        return "HIGH", Decimal("30")


# ── Public API ────────────────────────────────────────────────────────────────

def evaluate_risk(
    customer: Customer,
    application: LoanApplication,
) -> Tuple[str, Decimal, str, Decimal, Decimal]:
    """
    Returns: (risk_level, approval_probability, reason, recommended_amount, foir)
    Uses ML model when available, falls back to Phase 1 rules otherwise.
    """
    monthly_salary = Decimal(str(customer.monthly_salary))
    existing_emi = Decimal(str(customer.existing_emi))
    requested_amount = Decimal(str(application.requested_amount))
    tenure_months = application.tenure_months
    employment_type = customer.employment_type

    foir = calculate_foir(existing_emi, requested_amount, tenure_months, monthly_salary)
    foir_cap = get_foir_cap(employment_type)
    recommended_amount = calculate_recommended_amount(customer, tenure_months)

    if _model is not None:
        risk_level, approval_probability, reason = _ml_evaluate(customer, application, foir)
    else:
        risk_level, approval_probability = _rule_evaluate(customer, foir, foir_cap, customer.missed_payments)
        reason = _rule_reasons(customer, foir, foir_cap)

    return risk_level, approval_probability, reason, recommended_amount, foir


def retrain_model() -> dict:
    """
    Re-runs the training logic and reloads the model in-process instantly.
    Called by the admin retrain endpoint.
    """
    import sys
    ml_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml"))
    if ml_dir not in sys.path:
        sys.path.insert(0, ml_dir)
    import train_model
    output_msg = train_model.train_and_save_model()
    _load_model()
    return {"status": "retrained", "output": output_msg}
