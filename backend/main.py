"""
AutoWorth AI — FastAPI Application Entry Point

Creates and configures the FastAPI application:
- CORS middleware
- Exception handlers
- API router mounting
- OpenAPI documentation config

Business logic must NOT live here.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.logging import setup_logging
import structlog

settings = get_settings()


# ──────────────────────────────────────────────
# Lifespan Events
# ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application startup / shutdown lifecycle.

    Startup:
    - Warm the ML model cache by loading the active ModelVersion artifacts
      into memory so the first prediction request pays no cold-load penalty.
    """
    setup_logging()
    logger = structlog.get_logger()
    logger.info("application_startup", app=settings.APP_NAME, version=settings.APP_VERSION, env=settings.ENVIRONMENT)

    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting...")
    print(f"   Environment : {settings.ENVIRONMENT}")
    print(f"   Docs        : http://localhost:8000/docs")
    print(f"   API prefix  : /api/v1")

    # ── ML Model Cache Warm-Up ─────────────────────────────────
    try:
        from app.core.database import AsyncSessionLocal
        from app.services.ml_service import MLService

        async with AsyncSessionLocal() as db:
            ml_service = MLService()
            active = await ml_service.load_active_model(db)
            if active:
                print(
                    f"   🔥 ML model warmed  : version={active.version_tag} "
                    f"(R²={active.r2_score:.4f})"
                )
            else:
                print(
                    "   ⚠️  No active ML model found. "
                    "Train + activate a model via POST /api/v1/admin/models/train."
                )
    except Exception as exc:
        # Don't crash startup if the DB isn't ready (e.g., first-time setup)
        print(f"   ⚠️  ML model warm-up skipped: {exc}")

    yield

    # Shutdown
    print("🛑 AutoWorth AI shutting down...")


# ──────────────────────────────────────────────
# Application Factory
# ──────────────────────────────────────────────
def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "AI-Powered Vehicle Valuation Platform for India. "
            "Provides ML-based used car price predictions, "
            "Computer Vision damage analysis, and SHAP explainability."
        ),
        openapi_url="/openapi.json" if not settings.is_production else None,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.api.middleware import LoggingMiddleware
    application.add_middleware(LoggingMiddleware)

    # ── Global Exception Handlers ─────────────────────────────
    @application.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "message": "The requested resource was not found.",
                "error_code": "NOT_FOUND",
            },
        )

    @application.exception_handler(500)
    async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger = structlog.get_logger()
        logger.exception("internal_server_error", exc_info=exc, path=request.url.path)
        
        # Never expose stack traces in production
        message = (
            "An internal server error occurred. Please try again later."
            if settings.is_production
            else str(exc)
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": message,
                "error_code": "INTERNAL_SERVER_ERROR",
            },
        )

    # ── Routers ───────────────────────────────────────────────
    application.include_router(api_v1_router)

    # ── Root Redirect ─────────────────────────────────────────
    @application.get("/", include_in_schema=False)
    async def root() -> dict:
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "health": "/api/v1/health",
        }

    return application


app = create_application()
