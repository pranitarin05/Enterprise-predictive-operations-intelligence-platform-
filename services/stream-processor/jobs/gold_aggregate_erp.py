"""
Gold-layer aggregation job.

v3: adds daily_supplier_delay -- delay days attributed to the SPECIFIC
supplier whose shipment was delayed (from shipment_delayed events'
supplier field), rather than the whole tenant-day total. The earlier
version attributed a day's total delay to every supplier active that
day, which washed out the real per-supplier risk signal. This table
fixes that by aggregating strictly on shipment_delayed events, grouped
by their own supplier field.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from pyspark.sql.functions import (
    col, count, sum as spark_sum, avg, to_date, coalesce, lit,
)

from config.spark_session import get_spark_session
from config.settings import settings


def main():
    spark = get_spark_session("gold-aggregate-erp")

    silver_path = f"s3a://{settings.s3_bucket_silver}/erp_events"
    daily_summary_path = f"s3a://{settings.s3_bucket_gold}/daily_tenant_summary"
    supplier_summary_path = f"s3a://{settings.s3_bucket_gold}/supplier_spend_summary"
    supplier_activity_path = f"s3a://{settings.s3_bucket_gold}/daily_supplier_activity"
    supplier_delay_path = f"s3a://{settings.s3_bucket_gold}/daily_supplier_delay"

    silver_df = spark.read.format("delta").load(silver_path)
    print(f"Read {silver_df.count()} rows from Silver.")

    daily_summary_df = (
        silver_df
        .withColumn("event_date", to_date(col("event_time")))
        .groupBy("tenant_id", "event_date", "event_type")
        .agg(
            count("*").alias("event_count"),
            spark_sum(coalesce(col("amount_usd"), lit(0))).alias("total_amount_usd"),
            spark_sum(coalesce(col("delay_days"), lit(0))).alias("total_delay_days"),
            avg(col("quantity_remaining")).alias("avg_quantity_remaining"),
        )
        .orderBy("event_date", "event_type")
    )
    (daily_summary_df.write.format("delta").mode("overwrite")
        .option("overwriteSchema", "true").save(daily_summary_path))
    print(f"Wrote {daily_summary_df.count()} rows to {daily_summary_path}")

    supplier_summary_df = (
        silver_df
        .filter(col("event_type") == "purchase_order_created")
        .groupBy("tenant_id")
        .agg(
            count("*").alias("order_count"),
            spark_sum(coalesce(col("amount_usd"), lit(0))).alias("total_spend_usd"),
            avg(col("amount_usd")).alias("avg_order_value_usd"),
        )
    )
    (supplier_summary_df.write.format("delta").mode("overwrite")
        .option("overwriteSchema", "true").save(supplier_summary_path))
    print(f"Wrote {supplier_summary_df.count()} rows to {supplier_summary_path}")

    supplier_activity_df = (
        silver_df
        .filter((col("event_type") == "purchase_order_created") & col("supplier").isNotNull())
        .withColumn("event_date", to_date(col("event_time")))
        .groupBy("tenant_id", "event_date", "supplier")
        .agg(
            count("*").alias("order_count"),
            spark_sum(coalesce(col("amount_usd"), lit(0))).alias("order_value_usd"),
        )
    )
    (supplier_activity_df.write.format("delta").mode("overwrite")
        .option("overwriteSchema", "true").save(supplier_activity_path))
    print(f"Wrote {supplier_activity_df.count()} rows to {supplier_activity_path}")

    # --- New: delay days attributed to the SPECIFIC supplier that was delayed ---
    supplier_delay_df = (
        silver_df
        .filter((col("event_type") == "shipment_delayed") & col("supplier").isNotNull())
        .withColumn("event_date", to_date(col("event_time")))
        .groupBy("tenant_id", "event_date", "supplier")
        .agg(
            count("*").alias("delay_event_count"),
            spark_sum(coalesce(col("delay_days"), lit(0))).alias("supplier_delay_days"),
        )
    )
    (supplier_delay_df.write.format("delta").mode("overwrite")
        .option("overwriteSchema", "true").save(supplier_delay_path))
    print(f"Wrote {supplier_delay_df.count()} rows to {supplier_delay_path}")

    print("\nDaily supplier delay preview:")
    supplier_delay_df.orderBy(col("supplier_delay_days").desc()).show(10, truncate=False)


if __name__ == "__main__":
    main()
