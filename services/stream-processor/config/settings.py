"""
Lightweight settings loader for the stream-processor service.
Deliberately independent from apps/api's settings -- each service
owns its own configuration, a real microservice boundary.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_bronze: str = "epoip-bronze"

    kafka_bootstrap_servers: str = "localhost:9092"

    model_config = SettingsConfigDict(
        env_file="../../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
