"""
Prediction repository -- the ONLY place allowed to query the
predictions table.
"""

import uuid

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.prediction import Prediction


def create_prediction(
    db: Session,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    model_name: str,
    input_payload: dict,
    prediction_value: float,
    is_high_risk: bool,
    explanation: dict,
) -> Prediction:
    prediction = Prediction(
        tenant_id=tenant_id,
        user_id=user_id,
        model_name=model_name,
        input_payload=input_payload,
        prediction_value=prediction_value,
        is_high_risk=is_high_risk,
        explanation=explanation,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


def get_predictions_for_tenant(
    db: Session, tenant_id: uuid.UUID, limit: int = 50
) -> list[Prediction]:
    """
    RLS (from Phase 6) already restricts this at the database level to
    the current session's tenant -- this tenant_id filter is a second,
    explicit layer, consistent with our defense-in-depth approach.
    """
    return (
        db.query(Prediction)
        .filter(Prediction.tenant_id == tenant_id)
        .order_by(desc(Prediction.created_at))
        .limit(limit)
        .all()
    )
