"""
Simulates a stream of ERP events for local development and testing.

Real ERP integration would replace this script entirely, but the
downstream pipeline (Spark validation, Delta Lake, features) can be
built and tested completely without one, using this instead.
"""

import logging
import random
import sys
import time
import uuid
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.messaging.producer import publish_erp_event, flush_producer
from app.messaging.schemas import ERPEvent, ERPEventType

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("simulate_erp_events")

# A fixed tenant_id for testing -- in Step 9 you'll swap this for the real
# tenant_id you got back from registration earlier in this conversation.
TEST_TENANT_ID = "7855a80e-d84a-421d-961b-0e0a3d3a4bf4"

EVENT_GENERATORS = {
    ERPEventType.PURCHASE_ORDER_CREATED: lambda: {
        "supplier": random.choice(["Acme Supplies", "Global Parts Co", "FastTrack Logistics"]),
        "amount_usd": round(random.uniform(500, 50000), 2),
    },
    ERPEventType.SHIPMENT_DELAYED: lambda: {
        "reason": random.choice(["customs_hold", "weather", "carrier_capacity"]),
        "delay_days": random.randint(1, 14),
    },
    ERPEventType.INVENTORY_LOW_STOCK: lambda: {
        "sku": f"SKU-{random.randint(1000, 9999)}",
        "quantity_remaining": random.randint(0, 20),
    },
    ERPEventType.SUPPLIER_PRICE_CHANGE: lambda: {
        "percent_change": round(random.uniform(-15.0, 25.0), 2),
    },
}


def generate_random_event(tenant_id: str) -> ERPEvent:
    event_type = random.choice(list(ERPEventType))
    return ERPEvent(
        tenant_id=tenant_id,
        event_type=event_type,
        entity_id=str(uuid.uuid4()),
        payload=EVENT_GENERATORS[event_type](),
    )


def main(num_events: int = 20, delay_seconds: float = 0.5) -> None:
    logger.info(f"Simulating {num_events} ERP events for tenant {TEST_TENANT_ID}...")

    for i in range(num_events):
        event = generate_random_event(TEST_TENANT_ID)
        publish_erp_event(event)
        logger.info(f"[{i + 1}/{num_events}] Published: {event.event_type.value} ({event.entity_id})")
        time.sleep(delay_seconds)

    flush_producer()
    logger.info("Simulation complete. All messages flushed.")


if __name__ == "__main__":
    main()
