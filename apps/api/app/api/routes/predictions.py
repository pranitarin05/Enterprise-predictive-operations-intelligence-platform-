"""
Prediction routes.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.repositories import prediction_repository
from app.schemas.prediction import (
    ShipmentDelayPredictionRequest,
    ShipmentDelayPredictionResponse,
    PredictionHistoryItem,
)
from app.services.prediction_service import predict_shipment_delay

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.post("/shipment-delay", response_model=ShipmentDelayPredictionResponse)
def predict_shipment_delay_endpoint(
    payload: ShipmentDelayPredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    result = predict_shipment_delay(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        supplier=payload.supplier,
        amount_usd=payload.amount_usd,
    )
    return ShipmentDelayPredictionResponse(**result)


@router.get("/history", response_model=list[PredictionHistoryItem])
def get_prediction_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    limit: int = 50,
):
    predictions = prediction_repository.get_predictions_for_tenant(
        db=db, tenant_id=current_user.tenant_id, limit=limit
    )
    return predictions
