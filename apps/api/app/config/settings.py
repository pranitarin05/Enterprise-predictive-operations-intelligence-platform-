"""
Centralized application configuration.

Why this exists: instead of scattering os.environ.get("SOME_VAR") calls
across the codebase (error-prone, no validation, no defaults documented
in one place), every setting the app needs is declared once here, typed,
and validated at startup. If a required variable is missing or malformed,
the app fails immediately with a clear error instead of crashing later
mid-request.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- MinIO / S3-compatible storage ---
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_raw: str = "epoip-raw"
    s3_bucket_bronze: str = "epoip-bronze"
    s3_bucket_silver: str = "epoip-silver"
    s3_bucket_gold: str = "epoip-gold"

    # --- PostgreSQL ---
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "epoip"
    postgres_user: str = "epoip_user"
    postgres_password: str = "changeme"

    # --- Redis ---
    redis_host: str = "localhost"
    redis_port: int = 6379

    # --- Kafka ---
    kafka_bootstrap_servers: str = "localhost:9092"

    # --- Qdrant ---
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    # --- Auth (used later) ---
    jwt_secret_key: str = "change_this_to_a_random_64_char_string"
    jwt_algorithm: str = "HS256"

    @property
    def postgres_dsn(self) -> str:
        """Builds the full connection string SQLAlchemy needs."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    model_config = SettingsConfigDict(
        env_file="../../.env",   # path relative to where this file sits
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Single shared instance — imported everywhere else in the app
settings = Settings()
