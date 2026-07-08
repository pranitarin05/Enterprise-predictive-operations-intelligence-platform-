"""
Event schemas for data flowing through Kafka.

Defining these as Pydantic models (not just raw dicts) means every event
we produce is validated BEFORE it hits Kafka -- catching bad data at the
source instead of letting garbage flow downstream into Spark/Delta Lake.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ERPEventType(str, Enum):
    PURCHASE_ORDER_CREATED = "purchase_order_created"
    SHIPMENT_DELAYED = "shipment_delayed"
    INVENTORY_LOW_STOCK = "inventory_low_stock"
    SUPPLIER_PRICE_CHANGE = "supplier_price_change"


class ERPEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    event_type: ERPEventType
    entity_id: str  # e.g. a purchase order number or SKU
    payload: dict
    event_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_kafka_key(self) -> str:
        """
        Events for the same entity should land on the same partition,
        so consumers processing that entity's history see them in order.
        """
        return self.entity_id

    def to_kafka_value(self) -> str:
        """Serializes to a JSON string for the Kafka message body."""
        return self.model_dump_json()
