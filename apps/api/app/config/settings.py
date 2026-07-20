"""
Centralized application configuration.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_raw: str = "epoip-raw"
    s3_bucket_bronze: str = "epoip-bronze"
    s3_bucket_silver: str = "epoip-silver"
    s3_bucket_gold: str = "epoip-gold"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "epoip"
    postgres_user: str = "epoip_user"
    postgres_password: str = "changeme"

    redis_host: str = "localhost"
    redis_port: int = 6379

    kafka_bootstrap_servers: str = "localhost:9092"

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    jwt_secret_key: str = "change_this_to_a_random_64_char_string"
    jwt_algorithm: str = "HS256"

    # Comma-separated list, so multiple deployed frontend URLs can be
    # allowed at once if needed (e.g. staging + production).
    cors_allowed_origins: str = "http://localhost:3000"

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",")]

    model_config = SettingsConfigDict(
        env_file="../../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
