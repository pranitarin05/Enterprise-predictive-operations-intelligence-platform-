"""
Exports the Gold daily_tenant_summary Delta table to plain Parquet files.

Feast's offline store reads Parquet directly, not Delta's transaction-log
format -- this job produces a stable, Feast-readable snapshot. Run this
after gold_aggregate_erp.py completes.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from pyspark.sql.functions import col, to_timestamp
from pyspark.sql.types import DoubleType

from config.spark_session import get_spark_session
from config.settings import settings


def main():
    spark = get_spark_session("export-gold-to-parquet")

    gold_path = f"s3a://{settings.s3_bucket_gold}/daily_tenant_summary"
    parquet_path = f"s3a://{settings.s3_bucket_gold}/feast_exports/daily_tenant_summary"

    df = spark.read.format("delta").load(gold_path)

    # Feast requires a true TIMESTAMP for its timestamp_field, and plain
    # float/int types for numeric features -- it doesn't understand
    # Python's Decimal type (which Silver's precise DecimalType casting
    # produces). Both are Gold-table-correct choices; we adapt them here
    # specifically for Feast's consumption, without touching Gold itself.
    df_for_feast = (
        df
        .withColumn("event_date", to_timestamp(col("event_date")))
        .withColumn("total_amount_usd", col("total_amount_usd").cast(DoubleType()))
    )

    (
        df_for_feast.write.mode("overwrite")
        .parquet(parquet_path)
    )

    print(f"Exported {df_for_feast.count()} rows to {parquet_path}")


if __name__ == "__main__":
    main()
