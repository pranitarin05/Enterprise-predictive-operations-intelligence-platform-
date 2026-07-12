"""
Gold-layer per-order table: one row per purchase order, joined to its
matching shipment_delayed event (if any) via po_entity_id. This gives
an unambiguous, non-diluted label -- "was THIS specific order delayed"
-- unlike daily aggregation, where one day's mixed suppliers washed
out individual risk signal.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from pyspark.sql.functions import col, to_date, when, lit

from config.spark_session import get_spark_session
from config.settings import settings


def main():
    spark = get_spark_session("gold-order-level")

    silver_path = f"s3a://{settings.s3_bucket_silver}/erp_events"
    output_path = f"s3a://{settings.s3_bucket_gold}/order_level"

    silver_df = spark.read.format("delta").load(silver_path)

    orders = (
        silver_df.filter(col("event_type") == "purchase_order_created")
        .select(
            col("tenant_id"),
            col("entity_id").alias("po_entity_id"),
            col("supplier"),
            col("amount_usd"),
            to_date(col("event_time")).alias("order_date"),
        )
    )

    delays = (
        silver_df.filter(col("event_type") == "shipment_delayed")
        .select(
            col("po_entity_id").alias("delay_po_entity_id"),
            col("delay_days"),
        )
    )

    order_level = (
        orders.join(delays, orders.po_entity_id == delays.delay_po_entity_id, "left")
        .withColumn("was_delayed", when(col("delay_days").isNotNull(), lit(1)).otherwise(lit(0)))
        .withColumn("delay_days", when(col("delay_days").isNotNull(), col("delay_days")).otherwise(lit(0)))
        .select("tenant_id", "po_entity_id", "supplier", "amount_usd", "order_date", "was_delayed", "delay_days")
    )

    (order_level.write.format("delta").mode("overwrite")
        .option("overwriteSchema", "true").save(output_path))

    print(f"Wrote {order_level.count()} order-level rows to {output_path}")
    print(f"Overall delay rate: {order_level.selectExpr('avg(was_delayed)').first()[0]:.2%}")
    print("\nDelay rate by supplier:")
    order_level.groupBy("supplier").agg({"was_delayed": "avg", "po_entity_id": "count"}).show()


if __name__ == "__main__":
    main()
