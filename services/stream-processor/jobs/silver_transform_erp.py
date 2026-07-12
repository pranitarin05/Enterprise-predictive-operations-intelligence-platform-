"""
Silver-layer transformation job.
v3: extracts po_entity_id from shipment_delayed events, linking each
delay directly to its originating purchase order for per-order
prediction (avoiding daily-aggregation signal dilution).
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from pyspark.sql.functions import col, when, lit, count
from pyspark.sql.types import DecimalType, IntegerType

from config.spark_session import get_spark_session
from config.settings import settings

VALID_EVENT_TYPES = {
    "purchase_order_created", "shipment_delayed",
    "inventory_low_stock", "supplier_price_change",
}


def main():
    spark = get_spark_session("silver-transform-erp")

    bronze_path = f"s3a://{settings.s3_bucket_bronze}/erp_events"
    silver_path = f"s3a://{settings.s3_bucket_silver}/erp_events"
    dead_letter_path = f"s3a://{settings.s3_bucket_silver}/_dead_letter/erp_events"

    bronze_df = spark.read.format("delta").load(bronze_path)
    print(f"Read {bronze_df.count()} rows from Bronze.")

    deduped_df = bronze_df.dropDuplicates(["event_id"])
    duplicate_count = bronze_df.count() - deduped_df.count()
    print(f"Removed {duplicate_count} duplicate event_id(s).")

    validated_df = deduped_df.withColumn(
        "validation_error",
        when(col("event_type").isNull() | (~col("event_type").isin(list(VALID_EVENT_TYPES))),
             lit("unknown_event_type"))
        .when(col("tenant_id").isNull(), lit("missing_tenant_id"))
        .when(col("entity_id").isNull(), lit("missing_entity_id"))
        .when(col("event_time").isNull(), lit("missing_event_time"))
        .otherwise(lit(None)),
    )

    valid_df = validated_df.filter(col("validation_error").isNull()).drop("validation_error")
    invalid_df = validated_df.filter(col("validation_error").isNotNull())

    print(f"Valid: {valid_df.count()} | Invalid (dead-letter): {invalid_df.count()}")

    silver_df = (
        valid_df
        .withColumn("amount_usd", when(col("payload.amount_usd").isNotNull(),
                    col("payload.amount_usd").cast(DecimalType(12, 2))))
        .withColumn("delay_days", when(col("payload.delay_days").isNotNull(),
                    col("payload.delay_days").cast(IntegerType())))
        .withColumn("quantity_remaining", when(col("payload.quantity_remaining").isNotNull(),
                    col("payload.quantity_remaining").cast(IntegerType())))
        .withColumn("supplier", when(col("payload.supplier").isNotNull(), col("payload.supplier")))
        .withColumn("po_entity_id", when(col("payload.po_entity_id").isNotNull(), col("payload.po_entity_id")))
    )

    (silver_df.write.format("delta").mode("overwrite")
        .option("overwriteSchema", "true").save(silver_path))
    print(f"Wrote {silver_df.count()} rows to Silver at {silver_path}")

    if invalid_df.count() > 0:
        (invalid_df.write.format("delta").mode("overwrite")
            .option("overwriteSchema", "true").save(dead_letter_path))
        print(f"Wrote {invalid_df.count()} rows to dead-letter at {dead_letter_path}")
    else:
        print("No dead-letter records this run.")

    print("\nEvent type breakdown in Silver:")
    silver_df.groupBy("event_type").agg(count("*").alias("row_count")).show()


if __name__ == "__main__":
    main()
