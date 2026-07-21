"""
AutoWorth AI — API v1 Router

Aggregates all v1 endpoint routers under /api/v1.
Add new feature routers here as phases are implemented.
"""

from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router

# Phase 2 — Auth & User Management
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router

# Phase 3 — ML Predictions & Admin Model Management
from app.api.v1.endpoints.predictions import router as predictions_router
from app.api.v1.endpoints.admin import router as admin_router

# Phase 4 — Computer Vision
from app.api.v1.endpoints.cv import router as cv_router

# Phase 5 routers
# from app.api.v1.endpoints.reports import router as reports_router

api_v1_router = APIRouter(prefix="/api/v1")

# ── Active Routes ─────────────────────────────────────────────
api_v1_router.include_router(health_router)

# ── Phase 2 — Auth & User Management ─────────────────────────
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)

# ── Phase 3 — Predictions & Admin ─────────────────────────────
api_v1_router.include_router(predictions_router)
api_v1_router.include_router(admin_router)

# ── Phase 4 — Computer Vision ─────────────────────────────────
api_v1_router.include_router(cv_router)
