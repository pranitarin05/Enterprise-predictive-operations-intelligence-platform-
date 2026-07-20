"""
Prediction routes.
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.prediction import ShipmentDelayPredictionRequest, ShipmentDelayPredictionResponse
from app.services.prediction_service import predict_shipment_delay

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.post("/shipment-delay", response_model=ShipmentDelayPredictionResponse)
def predict_shipment_delay_endpoint(
    payload: ShipmentDelayPredictionRequest,
    current_user: User = Depends(get_current_user),
):
    result = predict_shipment_delay(payload.supplier, payload.amount_usd)
    return ShipmentDelayPredictionResponse(**result)
