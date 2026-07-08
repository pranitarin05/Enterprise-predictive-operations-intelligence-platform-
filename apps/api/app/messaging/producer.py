"""
Kafka producer wrapper.

This is the ONLY file that should ever import confluent_kafka's Producer
directly -- everything else in the app calls functions here, so if we ever
need to change delivery guarantees, retry logic, or the client library
itself, there's exactly one place to change it.
"""

import logging

from confluent_kafka import Producer

from app.config.settings import settings
from app.messaging.schemas import ERPEvent

logger = logging.getLogger("epoip.kafka.producer")

_producer_config = {
    "bootstrap.servers": settings.kafka_bootstrap_servers,
    "acks": "all",           # wait for all in-sync replicas to confirm -- strongest durability guarantee
    "retries": 5,
    "linger.ms": 10,         # small batching delay -- improves throughput under load
}

_producer = Producer(_producer_config)


def _delivery_callback(err, msg) -> None:
    """
    Called asynchronously by librdkafka once a message is actually
    delivered (or fails). This is how we know delivery succeeded,
    since produce() itself doesn't block waiting for confirmation.
    """
    if err is not None:
        logger.error(f"Message delivery failed: {err}")
    else:
        logger.info(
            f"Delivered to {msg.topic()} [partition {msg.partition()}] "
            f"at offset {msg.offset()}"
        )


def publish_erp_event(event: ERPEvent, topic: str = "raw.erp.events") -> None:
    """
    Publishes a single ERP event to Kafka.

    poll(0) is called to trigger any pending delivery callbacks without
    blocking -- this must be called periodically or callbacks never fire.
    """
    _producer.produce(
        topic=topic,
        key=event.to_kafka_key(),
        value=event.to_kafka_value(),
        callback=_delivery_callback,
    )
    _producer.poll(0)


def flush_producer(timeout: float = 10.0) -> None:
    """
    Blocks until all outstanding messages are delivered or the timeout
    expires. MUST be called before the application exits, or buffered
    messages can be silently lost.
    """
    remaining = _producer.flush(timeout)
    if remaining > 0:
        logger.warning(f"{remaining} messages were not delivered before flush timeout.")
