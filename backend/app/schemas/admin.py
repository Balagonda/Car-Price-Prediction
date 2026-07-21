"""
AutoWorth AI — Admin Schemas

Pydantic models for admin analytics, activity logs, and dataset management.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── Analytics & Health ────────────────────────────────────────

class HealthStatus(BaseModel):
    api_status: str = "operational"
    db_status: str = "operational"
    cloudinary_status: str = "operational"
    api_latency_ms: int = 0
    active_model_version: str | None = None
    uptime_seconds: float = 0.0

class ChartData(BaseModel):
    name: str
    count: int

class AnalyticsKPIs(BaseModel):
    total_users: int = 0
    active_users: int = 0
    total_predictions: int = 0
    predictions_today: int = 0
    success_rate_percent: float = 0.0
    most_searched_brands: list[ChartData] = []
    city_breakdowns: list[ChartData] = []

class AnalyticsResponse(BaseModel):
    kpis: AnalyticsKPIs
    health: HealthStatus

# ── Activity Log ──────────────────────────────────────────────

class ActivityLogResponse(BaseModel):
    id: uuid.UUID
    action: str
    entity_type: str | None
    entity_id: str | None
    ip_address: str | None
    extra_data: str | None
    user_id: uuid.UUID | None
    created_at: datetime

# ── Dataset ───────────────────────────────────────────────────

class DatasetUploadResponse(BaseModel):
    dataset_id: uuid.UUID
    name: str
    version: str
    row_count: int
    column_count: int
    duplicate_rows_removed: int
    invalid_rows_removed: int
    message: str
