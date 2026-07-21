"""
AutoWorth AI — Health Check Endpoint

Provides API and database status.
No authentication required — used by deployment platforms and monitoring tools.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    summary="Health Check",
    description="Returns the API status, version, and database connectivity.",
)
async def health_check(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """
    Health check endpoint.

    Returns:
        - api_status: always "ok" if the server is running
        - db_status: "ok" if PostgreSQL connection is healthy
        - version: current application version
        - environment: development | staging | production
        - timestamp: current UTC time
    """
    # Verify database connectivity
    db_status = "ok"
    db_error: str | None = None
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = "error"
        db_error = str(exc) if not settings.is_production else "Database unavailable"

    return {
        "api_status": "ok",
        "db_status": db_status,
        "db_error": db_error,
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(UTC).isoformat(),
    }
