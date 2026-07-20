"""
Pydantic schemas for the prediction endpoint.
"""

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
