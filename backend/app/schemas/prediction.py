"""
AutoWorth AI — Prediction Schemas

Pydantic v2 schemas for prediction requests and responses.
"""

import uuid
from datetime import datetime

from pydantic import Field

from app.models.vehicle import (
    FuelType,
    InsuranceStatus,
    OwnerType,
    SellerType,
    TransmissionType,
    VehicleCategory,
)
from app.schemas.common import BaseSchema


# ──────────────────────────────────────────────
# Request Schemas
# ──────────────────────────────────────────────
class PredictionRequest(BaseSchema):
    """Input schema for vehicle price prediction."""

    # Vehicle taxonomy
    brand_id: int
    car_model_id: int
    variant_id: int | None = None
    city_id: int | None = None

    # Core specs
    manufacturing_year: int = Field(..., ge=1990, le=2025)
    fuel_type: FuelType
    transmission: TransmissionType
    owner_type: OwnerType
    seller_type: SellerType
    category: VehicleCategory

    # Numeric specs
    kilometers_driven: int = Field(..., ge=0, le=1_000_000)
    engine_cc: int | None = Field(None, ge=50, le=10_000)
    mileage_kmpl: float | None = Field(None, ge=0.0, le=100.0)
    seats: int | None = Field(None, ge=1, le=14)
    max_power_bhp: float | None = Field(None, ge=0.0, le=2000.0)

    # Condition
    insurance_status: InsuranceStatus


# ──────────────────────────────────────────────
# Response Schemas
# ──────────────────────────────────────────────
class ShapFeatureResponse(BaseSchema):
    """A single SHAP feature contribution entry."""

    feature_name: str
    raw_feature_name: str | None = None
    feature_value: str | None = None
    shap_value: float
    impact_direction: str                    # "positive" | "negative"
    rank: int
    human_readable_impact: str | None = None
    impact_percentage: float | None = None   # % of total estimated price


class SimilarVehicleResponse(BaseSchema):
    """A comparable historical vehicle returned by the KNN similarity engine."""

    brand: str
    model: str
    manufacturing_year: int
    fuel_type: str
    transmission: str
    owner_type: str
    kilometers_driven: int
    selling_price: float
    similarity_score: float  # 0–100 %


class RecommendationResponse(BaseSchema):
    title: str
    description: str
    priority: str
    display_order: int


class PredictionResponse(BaseSchema):
    """Full prediction response including SHAP, similar vehicles, and confidence."""

    id: uuid.UUID
    estimated_price: float
    confidence_score: float          # 0–100 %
    confidence_warning: str | None   # Non-null when confidence < 60%
    price_range_min: float
    price_range_max: float
    fair_price_status: str
    depreciation_percent: float | None
    showroom_price: float | None

    # Explainability
    shap_results: list[ShapFeatureResponse] = []
    similar_vehicles: list[SimilarVehicleResponse] = []

    # Recommendations
    recommendations: list[RecommendationResponse] = []

    # Computer Vision (Phase 4)
    cv_damage_detected: bool | None = None
    cv_damage_severity: str | None = None
    cv_repair_cost_estimate: float | None = None

    # Report
    is_pdf_generated: bool = False
    pdf_url: str | None = None

    created_at: datetime


class PredictionListItem(BaseSchema):
    """Lightweight prediction summary for history/dashboard lists."""

    id: uuid.UUID
    estimated_price: float
    confidence_score: float
    fair_price_status: str
    created_at: datetime


# ──────────────────────────────────────────────
# Admin: Training Schemas
# ──────────────────────────────────────────────
class TrainingRequest(BaseSchema):
    """Admin request to trigger the offline training pipeline."""

    dataset_path: str = Field(
        ...,
        description="Absolute or relative path to the CSV dataset on the server.",
        examples=["./data/cars_india_v3.csv"],
    )
    version_tag: str = Field(
        ...,
        description="Human-readable version label, e.g. 'v2.1'.",
        min_length=1,
        max_length=50,
        examples=["v2.1"],
    )
    dataset_id: str | None = Field(
        None,
        description="UUID of an existing Dataset record to link to this version.",
    )


class TrainingResponse(BaseSchema):
    """Training pipeline result returned after a successful training run."""

    model_version_id: str
    version_tag: str
    r2_score: float
    rmse: float
    mae: float
    cross_val_score: float
    training_time_seconds: float
    training_samples: int
    model_artifact_path: str
    preprocessor_path: str
    low_confidence: bool
    message: str


# ──────────────────────────────────────────────
# Admin: Model Version Schemas
# ──────────────────────────────────────────────
class ModelVersionResponse(BaseSchema):
    """ModelVersion serialization for admin list/detail views."""

    id: uuid.UUID
    version_tag: str
    status: str
    r2_score: float | None
    rmse: float | None
    mae: float | None
    cross_val_score: float | None
    training_time_seconds: float | None
    training_samples: int | None
    model_artifact_path: str | None
    preprocessor_path: str | None
    notes: str | None
    created_at: datetime


class MLModelResponse(BaseSchema):
    """MLModel with its version history for the admin panel."""

    id: int
    name: str
    description: str | None
    is_active: bool
    versions: list[ModelVersionResponse] = []
    created_at: datetime
