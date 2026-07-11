"""
Gold-layer aggregation job.

Reads Silver ERP events and produces pre-computed, dashboard/ML-ready
summary tables:
  1. daily_tenant_summary  -- one row per tenant per day per event type,
     with counts and sums -- the core metric table dashboards will query.
  2. supplier_spend_summary -- total purchase order spend per supplier,
     a business-relevant rollup used later for supplier risk features.

This is a BATCH job, same pattern as Silver -- run on a schedule via
Airflow, reprocessing the full Silver table each run for now.
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

    silver_df = spark.read.format("delta").load(silver_path)
    print(f"Read {silver_df.count()} rows from Silver.")

    # --- Aggregation 1: daily counts + sums per tenant per event type ---
    # This is the core metric table -- "how many of each event type,
    # and how much money/impact, per tenant per day."
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

    (
        daily_summary_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .save(daily_summary_path)
    )
    print(f"Wrote {daily_summary_df.count()} rows to {daily_summary_path}")

    # --- Aggregation 2: supplier spend rollup ---
    # Only purchase_order_created events have a supplier -- this pulls
    # that subset and rolls up total spend, a business-meaningful metric
    # and a natural future ML feature (e.g. "supplier risk score").
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

    (
        supplier_summary_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .save(supplier_summary_path)
    )
    print(f"Wrote {supplier_summary_df.count()} rows to {supplier_summary_path}")

    print("\nDaily tenant summary preview:")
    daily_summary_df.show(10, truncate=False)

    print("\nSupplier spend summary preview:")
    supplier_summary_df.show(10, truncate=False)


if __name__ == "__main__":
    main()
