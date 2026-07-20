"""
Prediction model -- stores every prediction made through the API,
with its SHAP explanation, for history/audit/dashboard purposes.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    input_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    prediction_value: Mapped[float] = mapped_column(Float, nullable=False)
    is_high_risk: Mapped[bool] = mapped_column(Boolean, nullable=False)
    explanation: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<Prediction id={self.id} model={self.model_name!r} value={self.prediction_value}>"
