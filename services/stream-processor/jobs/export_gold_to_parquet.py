import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from pyspark.sql.functions import col, to_timestamp
from pyspark.sql.types import DoubleType

from config.spark_session import get_spark_session
from config.settings import settings


def export_table(spark, gold_path: str, parquet_path: str, date_col: str = None, amount_cols: list = None):
    df = spark.read.format("delta").load(gold_path)
    if date_col and date_col in df.columns:
        df = df.withColumn(date_col, to_timestamp(col(date_col)))
    if amount_cols:
        for c in amount_cols:
            if c in df.columns:
                df = df.withColumn(c, col(c).cast(DoubleType()))
    df.write.mode("overwrite").parquet(parquet_path)
    print(f"Exported {df.count()} rows to {parquet_path}")


def main():
    spark = get_spark_session("export-gold-to-parquet")
    export_table(spark, f"s3a://{settings.s3_bucket_gold}/daily_tenant_summary",
                 f"s3a://{settings.s3_bucket_gold}/feast_exports/daily_tenant_summary",
                 date_col="event_date", amount_cols=["total_amount_usd"])
    export_table(spark, f"s3a://{settings.s3_bucket_gold}/order_level",
                 f"s3a://{settings.s3_bucket_gold}/feast_exports/order_level",
                 date_col="order_date", amount_cols=["amount_usd"])


if __name__ == "__main__":
    main()
