"""
Simulates a richer stream of ERP events for local development and model
training. Bakes in an intentional, learnable (but noisy) pattern:
shipments from certain suppliers, combined with certain delay reasons,
have measurably higher delay risk -- this gives the training pipeline
a genuine signal to learn, rather than pure randomness.

Real ERP integration would replace this script entirely; this exists to
prove the ingestion -> training pipeline works correctly before any real
company's data flows through it.
"""

import logging
import random
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.messaging.producer import publish_erp_event, flush_producer
from app.messaging.schemas import ERPEvent, ERPEventType

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("simulate_erp_events")

TEST_TENANT_ID = "7855a80e-d84a-421d-961b-0e0a3d3a4bf4"

HIGH_RISK_SUPPLIERS = {"Global Parts Co", "FastTrack Logistics"}
LOW_RISK_SUPPLIERS = {"Acme Supplies", "Reliable Freight Inc", "Prime Vendor Group"}
ALL_SUPPLIERS = list(HIGH_RISK_SUPPLIERS | LOW_RISK_SUPPLIERS)

HIGH_RISK_REASONS = ["customs_hold", "carrier_capacity"]
LOW_RISK_REASONS = ["weather"]
ALL_REASONS = HIGH_RISK_REASONS + LOW_RISK_REASONS


def generate_purchase_order(event_time: datetime, supplier: str) -> ERPEvent:
    return ERPEvent(
        tenant_id=TEST_TENANT_ID,
        event_type=ERPEventType.PURCHASE_ORDER_CREATED,
        entity_id=str(uuid.uuid4()),
        payload={
            "supplier": supplier,
            "amount_usd": round(random.uniform(500, 50000), 2),
        },
        event_time=event_time,
    )


def generate_shipment_event(event_time: datetime, supplier: str) -> ERPEvent | None:
    is_high_risk_supplier = supplier in HIGH_RISK_SUPPLIERS
    reason = random.choice(HIGH_RISK_REASONS if is_high_risk_supplier else ALL_REASONS)
    is_high_risk_reason = reason in HIGH_RISK_REASONS

    delay_probability = 0.15
    if is_high_risk_supplier:
        delay_probability += 0.35
    if is_high_risk_reason:
        delay_probability += 0.25

    if random.random() > delay_probability:
        return None

    delay_days = random.randint(5, 14) if (is_high_risk_supplier and is_high_risk_reason) else random.randint(1, 5)

    return ERPEvent(
        tenant_id=TEST_TENANT_ID,
        event_type=ERPEventType.SHIPMENT_DELAYED,
        entity_id=str(uuid.uuid4()),
        payload={"reason": reason, "delay_days": delay_days},
        event_time=event_time,
    )


def generate_inventory_event(event_time: datetime) -> ERPEvent:
    return ERPEvent(
        tenant_id=TEST_TENANT_ID,
        event_type=ERPEventType.INVENTORY_LOW_STOCK,
        entity_id=str(uuid.uuid4()),
        payload={
            "sku": f"SKU-{random.randint(1000, 9999)}",
            "quantity_remaining": random.randint(0, 20),
        },
        event_time=event_time,
    )


def main(num_days: int = 60, orders_per_day: int = 8) -> None:
    logger.info(f"Simulating {num_days} days of ERP events for tenant {TEST_TENANT_ID}...")

    start_date = datetime.now(timezone.utc) - timedelta(days=num_days)
    total_published = 0

    for day_offset in range(num_days):
        event_time = start_date + timedelta(days=day_offset)

        for _ in range(orders_per_day):
            supplier = random.choice(ALL_SUPPLIERS)

            po_event = generate_purchase_order(event_time, supplier)
            publish_erp_event(po_event)
            total_published += 1

            shipment_event = generate_shipment_event(event_time, supplier)
            if shipment_event:
                publish_erp_event(shipment_event)
                total_published += 1

        for _ in range(2):
            publish_erp_event(generate_inventory_event(event_time))
            total_published += 1

        if day_offset % 10 == 0:
            logger.info(f"Day {day_offset}/{num_days} simulated ({total_published} events so far)...")

    flush_producer()
    logger.info(f"Simulation complete. {total_published} total events published and flushed.")


if __name__ == "__main__":
    main()
