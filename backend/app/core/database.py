"""
AutoWorth AI — Async Database Session Management

This module is infrastructure only:
- Creates the async SQLAlchemy engine
- Provides the session factory
- Exposes `get_db` as a FastAPI dependency

Business logic must NOT live here.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

settings = get_settings()

# ──────────────────────────────────────────────
# Async Engine
# ──────────────────────────────────────────────
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

db_url = settings.DATABASE_URL
connect_args = {}

url_parts = urlparse(db_url)
query_params = parse_qs(url_parts.query)

if "sslmode" in query_params or "neon.tech" in url_parts.netloc:
    for param in ["sslmode", "channel_binding", "sslrootcert", "target_session_attrs"]:
        query_params.pop(param, None)
    new_query = urlencode(query_params, doseq=True)
    url_parts = url_parts._replace(query=new_query)
    db_url = urlunparse(url_parts)
    connect_args["ssl"] = True
    connect_args["statement_cache_size"] = 0

engine = create_async_engine(
    db_url,
    echo=settings.DEBUG,          # Logs SQL queries in development
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,           # Verify connection before checkout
    pool_recycle=3600,            # Recycle connections after 1 hour
    connect_args=connect_args,
)

# ──────────────────────────────────────────────
# Async Session Factory
# ──────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,       # Prevents lazy-load errors post-commit
    autoflush=False,
    autocommit=False,
)


# ──────────────────────────────────────────────
# FastAPI Dependency
# ──────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a database session per request.

    Usage in FastAPI route:
        async def my_route(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
