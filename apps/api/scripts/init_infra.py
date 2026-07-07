"""
One-time (idempotent) infrastructure setup script.

Run this after `docker compose up` to create:
  - MinIO buckets for the medallion lakehouse layers (raw/bronze/silver/gold)
  - Kafka topics for raw data ingestion

Idempotent means: safe to run multiple times. If a bucket/topic already
exists, it's skipped rather than causing an error — this matters because
in a real team, multiple people (and CI) will run this script repeatedly.
"""

import logging
import sys
from pathlib import Path

# Allow running this script directly without installing the app as a package
sys.path.append(str(Path(__file__).resolve().parent.parent))

import boto3
from botocore.exceptions import ClientError
from confluent_kafka.admin import AdminClient, NewTopic

from app.config.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("init_infra")


def create_minio_buckets() -> None:
    """Creates the four medallion-architecture buckets in MinIO if they don't exist."""
    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
    )

    buckets = [
        settings.s3_bucket_raw,
        settings.s3_bucket_bronze,
        settings.s3_bucket_silver,
        settings.s3_bucket_gold,
    ]

    for bucket_name in buckets:
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"Bucket already exists, skipping: {bucket_name}")
        except ClientError:
            # head_bucket raises an error if the bucket doesn't exist yet — expected path for first run
            s3_client.create_bucket(Bucket=bucket_name)
            logger.info(f"Created bucket: {bucket_name}")


def create_kafka_topics() -> None:
    """Creates the initial raw-ingestion Kafka topics if they don't exist."""
    admin_client = AdminClient({"bootstrap.servers": settings.kafka_bootstrap_servers})

    topic_definitions = [
        NewTopic("raw.erp.events", num_partitions=3, replication_factor=1),
        NewTopic("raw.crm.events", num_partitions=3, replication_factor=1),
        NewTopic("raw.sensors.telemetry", num_partitions=6, replication_factor=1),
        NewTopic("raw.cloudlogs.events", num_partitions=3, replication_factor=1),
    ]

    existing_topics = admin_client.list_topics(timeout=10).topics.keys()

    topics_to_create = [t for t in topic_definitions if t.topic not in existing_topics]

    if not topics_to_create:
        logger.info("All Kafka topics already exist, skipping.")
        return

    futures = admin_client.create_topics(topics_to_create)
    for topic_name, future in futures.items():
        try:
            future.result()  # blocks until this specific topic creation completes
            logger.info(f"Created Kafka topic: {topic_name}")
        except Exception as e:
            logger.error(f"Failed to create topic {topic_name}: {e}")


def main() -> None:
    logger.info("Starting infrastructure initialization...")
    create_minio_buckets()
    create_kafka_topics()
    logger.info("Infrastructure initialization complete.")


if __name__ == "__main__":
    main()
