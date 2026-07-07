"""
Shared SQLAlchemy declarative base.

Every model class inherits from this Base. Alembic uses Base.metadata
to know what tables SHOULD exist, and compares that against what
ACTUALLY exists in the database to auto-generate migration scripts.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
