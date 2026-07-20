"""
Prediction service -- business logic for shipment delay risk scoring.

Uses the raw xgboost Booster API (DMatrix + predict) rather than the
sklearn wrapper (predict_proba), since we load the model as a Booster
directly (see app/ml/model_registry.py for why).
"""

import pandas as pd
import xgboost as xgb

from app.ml.model_registry import get_model, get_supplier_risk_score
from app.ml.explainer import explain_prediction

RISK_THRESHOLD = 0.35


def predict_shipment_delay(supplier: str, amount_usd: float) -> dict:
    model = get_model()

    supplier_risk_score = get_supplier_risk_score(supplier)
    features_df = pd.DataFrame([{
        "supplier_risk_score": supplier_risk_score,
        "amount_usd": amount_usd,
    }])

    dmatrix = xgb.DMatrix(features_df)
    # For a binary:logistic objective, Booster.predict() returns the
    # probability of the positive class directly (not raw margins).
    delay_probability = float(model.predict(dmatrix)[0])
    is_high_risk = delay_probability >= RISK_THRESHOLD

    explanation = explain_prediction(model, features_df)

    top_driver = max(explanation, key=lambda k: abs(explanation[k]))
    direction = "increases" if explanation[top_driver] > 0 else "decreases"
    explanation_summary = (
        f"{top_driver.replace('_', ' ')} {direction} delay risk the most "
        f"for this prediction (contribution: {explanation[top_driver]:+.4f})."
    )

    return {
        "supplier": supplier,
        "amount_usd": amount_usd,
        "delay_probability": round(delay_probability, 4),
        "is_high_risk": is_high_risk,
        "explanation": explanation,
        "explanation_summary": explanation_summary,
    }
