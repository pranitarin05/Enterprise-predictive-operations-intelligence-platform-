"""
SQLAlchemy engine and session management.

Why a single shared engine: creating a new database connection per request
is slow and wasteful. SQLAlchemy's engine manages a connection pool —
connections are reused across requests, opened lazily, and recycled safely.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.config.settings import settings

engine = create_engine(
    settings.postgres_dsn,
    pool_pre_ping=True,   # checks a connection is still alive before using it
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session() -> Session:
    """
    FastAPI dependency — yields a DB session per request and always closes it
    afterward, even if the request raised an exception.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Used by the health check — runs the simplest possible query."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
