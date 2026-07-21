"""
AutoWorth AI — Alembic Migration Environment

Configures Alembic for ASYNC SQLAlchemy with PostgreSQL.
Reads DATABASE_URL from pydantic-settings (never hardcoded).
Imports ALL models so autogenerate detects every table.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ── Load app settings ─────────────────────────────────────────
from app.core.config import get_settings

# ── Import ALL models (required for autogenerate) ─────────────
import app.models  # noqa: F401  — triggers all model imports via __init__.py
from app.models.base import Base

settings = get_settings()

# ── Alembic Config Object ─────────────────────────────────────
config = context.config

# Inject the DATABASE_URL from settings (overrides alembic.ini blank value)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Setup Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The metadata object for 'autogenerate'
target_metadata = Base.metadata


# ──────────────────────────────────────────────
# Offline Migrations (no live DB connection)
# ──────────────────────────────────────────────
def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    Generates SQL scripts without a DB connection.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ──────────────────────────────────────────────
# Online Migrations (async connection to live DB)
# ──────────────────────────────────────────────
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using asyncio."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
