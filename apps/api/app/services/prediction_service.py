"""
Prediction service -- business logic for shipment delay risk scoring.
Persists every prediction to the database for history/audit purposes.
"""

import uuid

import pandas as pd
import xgboost as xgb
from sqlalchemy.orm import Session

from app.ml.model_registry import get_model, get_supplier_risk_score
from app.ml.explainer import explain_prediction
from app.repositories import prediction_repository

RISK_THRESHOLD = 0.35
MODEL_NAME = "shipment_delay_predictor"


def predict_shipment_delay(
    db: Session,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    supplier: str,
    amount_usd: float,
) -> dict:
    model = get_model()

    supplier_risk_score = get_supplier_risk_score(supplier)
    features_df = pd.DataFrame([{
        "supplier_risk_score": supplier_risk_score,
        "amount_usd": amount_usd,
    }])

    dmatrix = xgb.DMatrix(features_df)
    delay_probability = float(model.predict(dmatrix)[0])
    is_high_risk = delay_probability >= RISK_THRESHOLD

    explanation = explain_prediction(model, features_df)

    top_driver = max(explanation, key=lambda k: abs(explanation[k]))
    direction = "increases" if explanation[top_driver] > 0 else "decreases"
    explanation_summary = (
        f"{top_driver.replace('_', ' ')} {direction} delay risk the most "
        f"for this prediction (contribution: {explanation[top_driver]:+.4f})."
    )

    # Persist -- every prediction becomes real, queryable history.
    prediction_repository.create_prediction(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        model_name=MODEL_NAME,
        input_payload={"supplier": supplier, "amount_usd": amount_usd},
        prediction_value=round(delay_probability, 4),
        is_high_risk=is_high_risk,
        explanation=explanation,
    )

    return {
        "supplier": supplier,
        "amount_usd": amount_usd,
        "delay_probability": round(delay_probability, 4),
        "is_high_risk": is_high_risk,
        "explanation": explanation,
        "explanation_summary": explanation_summary,
    }
