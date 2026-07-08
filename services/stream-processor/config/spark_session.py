"""
Builds a SparkSession configured for:
  - Delta Lake table format
  - MinIO as the S3-compatible storage backend (S3A connector)

This is the ONLY place Spark session configuration lives -- every job
imports get_spark_session() instead of building its own, so all jobs
stay consistently configured.
"""

from pyspark.sql import SparkSession

from config.settings import settings

# Maven coordinates for packages Spark needs to download at startup.
# These provide: Kafka streaming source, Delta Lake, and S3A (MinIO) support.
SPARK_PACKAGES = ",".join([
    "io.delta:delta-spark_2.12:3.2.0",
    "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3",
    "org.apache.hadoop:hadoop-aws:3.3.4",
    "com.amazonaws:aws-java-sdk-bundle:1.12.262",
])


def get_spark_session(app_name: str) -> SparkSession:
    builder = (
        SparkSession.builder.appName(app_name)
        .config("spark.jars.packages", SPARK_PACKAGES)
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        # --- MinIO / S3A configuration ---
        .config("spark.hadoop.fs.s3a.endpoint", settings.s3_endpoint_url)
        .config("spark.hadoop.fs.s3a.access.key", settings.s3_access_key)
        .config("spark.hadoop.fs.s3a.secret.key", settings.s3_secret_key)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config(
            "spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem"
        )
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
    )
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")  # Spark's default logging is very noisy
    return spark
