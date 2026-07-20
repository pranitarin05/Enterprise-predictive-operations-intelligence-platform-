"""
Pydantic schemas for the prediction endpoints.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ShipmentDelayPredictionRequest(BaseModel):
    supplier: str = Field(..., description="Supplier name for this order")
    amount_usd: float = Field(..., gt=0, description="Order value in USD")


class ShipmentDelayPredictionResponse(BaseModel):
    supplier: str
    amount_usd: float
    delay_probability: float
    is_high_risk: bool
    explanation: dict[str, float]
    explanation_summary: str


class PredictionHistoryItem(BaseModel):
    id: uuid.UUID
    model_name: str
    input_payload: dict
    prediction_value: float
    is_high_risk: bool
    explanation: dict
    created_at: datetime

    model_config = {"from_attributes": True}
