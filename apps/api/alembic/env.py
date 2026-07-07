"""
Alembic environment configuration.

This file runs every time you execute `alembic revision --autogenerate`
or `alembic upgrade`. It connects Alembic to:
  1. Our actual database (via app settings, not a hardcoded URL)
  2. Our SQLAlchemy models (so autogenerate can detect schema changes)
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# --- Import our app's settings and models ---
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.config.settings import settings
from app.models.base import Base
from app.models import tenant, role, user  # noqa: F401 — imported so Base knows about them

# Alembic Config object, gives access to values in alembic.ini
config = context.config

# Override the sqlalchemy.url from alembic.ini with our real settings
config.set_main_option("sqlalchemy.url", settings.postgres_dsn)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# This is what Alembic compares the live DB against to detect changes
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Generates SQL scripts without a live DB connection (rarely used by us)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connects to the real database and applies migrations directly. This is what we use."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
