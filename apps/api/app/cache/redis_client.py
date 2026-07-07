"""
Redis client setup — single shared connection pool for the whole app.
"""

import redis

from app.config.settings import settings

redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    decode_responses=True,   # returns strings instead of raw bytes
    socket_connect_timeout=3,
)


def check_redis_connection() -> bool:
    """Used by the health check."""
    try:
        return redis_client.ping()
    except Exception:
        return False
