"""
Bronze-layer streaming ingestion job.

Reads raw JSON events continuously from the raw.erp.events Kafka topic,
parses them against our known schema, and appends them to a Delta Lake
table on MinIO. This is intentionally "Bronze" -- minimal transformation,
just structured and durably stored. Cleaning/validation logic (Silver)
comes in a later phase.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StructField, StringType, MapType, TimestampType

from config.spark_session import get_spark_session
from config.settings import settings

# Mirrors app/messaging/schemas.py's ERPEvent -- kept in sync manually for now;
# a shared schema registry is a natural future improvement, noted here honestly
# rather than pretending this duplication doesn't exist.
ERP_EVENT_SCHEMA = StructType([
    StructField("event_id", StringType(), nullable=False),
    StructField("tenant_id", StringType(), nullable=False),
    StructField("event_type", StringType(), nullable=False),
    StructField("entity_id", StringType(), nullable=False),
    StructField("payload", MapType(StringType(), StringType()), nullable=True),
    StructField("event_time", TimestampType(), nullable=False),
])


def main():
    spark = get_spark_session("bronze-ingest-erp")

    raw_stream = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", settings.kafka_bootstrap_servers)
        .option("subscribe", "raw.erp.events")
        .option("startingOffsets", "earliest")
        .load()
    )

    # Kafka messages arrive as raw bytes in a column called "value" --
    # we cast to string, then parse the JSON against our known schema.
    parsed_stream = (
        raw_stream.selectExpr("CAST(value AS STRING) AS json_value")
        .select(from_json(col("json_value"), ERP_EVENT_SCHEMA).alias("data"))
        .select("data.*")
    )

    bronze_path = f"s3a://{settings.s3_bucket_bronze}/erp_events"
    checkpoint_path = f"s3a://{settings.s3_bucket_bronze}/_checkpoints/erp_events"

    query = (
        parsed_stream.writeStream.format("delta")
        .outputMode("append")
        .option("checkpointLocation", checkpoint_path)
        .start(bronze_path)
    )

    print(f"Streaming to {bronze_path} -- checkpoint at {checkpoint_path}")
    print("Press Ctrl+C to stop.")
    query.awaitTermination()


if __name__ == "__main__":
    main()
