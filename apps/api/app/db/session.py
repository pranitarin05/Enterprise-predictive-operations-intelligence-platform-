"""
SQLAlchemy engine and session management.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.config.settings import settings

engine = create_engine(
    settings.postgres_dsn,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session() -> Session:
    """
    FastAPI dependency -- yields a DB session per request and always closes it
    afterward, even if the request raised an exception.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def set_tenant_context(db: Session, tenant_id: str) -> None:
    """
    Sets the Postgres session variable that our Row-Level Security policy
    checks against (see infra/docker/postgres-init/02-rls.sql).

    Uses SET LOCAL -- scoped to the current transaction only, automatically
    reset afterward, so one request's tenant context can never leak into
    another request reusing a pooled connection.
    """
    db.execute(text("SET LOCAL app.current_tenant = :tenant_id"), {"tenant_id": tenant_id})


def check_db_connection() -> bool:
    """Used by the health check -- runs the simplest possible query."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
