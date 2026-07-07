"""
Health service — business logic for the health check endpoint.

This is intentionally the ONLY place that decides what "healthy" means.
The route below just calls this and returns whatever it says — it doesn't
know or care how each dependency is actually checked.
"""

from app.db.session import check_db_connection
from app.cache.redis_client import check_redis_connection
from app.storage.s3_client import check_storage_connection


def get_health_status() -> dict:
    db_ok = check_db_connection()
    redis_ok = check_redis_connection()
    storage_ok = check_storage_connection()

    all_healthy = db_ok and redis_ok and storage_ok

    return {
        "status": "healthy" if all_healthy else "degraded",
        "dependencies": {
            "database": "up" if db_ok else "down",
            "cache": "up" if redis_ok else "down",
            "storage": "up" if storage_ok else "down",
        },
    }
