"""
AutoWorth AI — CV Schemas (Phase 4)

Pydantic v2 schemas for the Computer Vision analysis API.

Layer: Schema Layer
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.common import BaseSchema


# ── Per-Part Detail ──────────────────────────────────────────────────────────

class DamagedPartDetail(BaseSchema):
    """Damage assessment result for a single vehicle body part."""

    part_name: str = Field(..., examples=["Front Bumper", "Hood"])
    severity: str = Field(
        ...,
        description="Damage severity for this part.",
        examples=["None", "Minor", "Moderate", "Severe"],
    )
    damage_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Raw composite damage score (0 = no damage, 1 = maximum).",
    )
    is_damaged: bool
    repair_cost_min: int = Field(..., description="Minimum repair cost estimate in INR.")
    repair_cost_max: int = Field(..., description="Maximum repair cost estimate in INR.")
    repair_cost_midpoint: float = Field(
        ..., description="Midpoint of the repair cost range in INR."
    )
    bbox: list[int] = Field(
        ...,
        description="Bounding box [x, y, w, h] of the part in the analysed image.",
    )


# ── Per-Image Upload Result ────────────────────────────────────────────────────

class ImageUploadResult(BaseSchema):
    """Result of a single image upload + CV analysis."""

    angle: str = Field(..., description="Image angle label (e.g., Front, Rear).")
    is_primary: bool = Field(
        ...,
        description="True if this image was selected as the primary image for CV analysis.",
    )
    cloudinary_url: str = Field(..., description="Secure Cloudinary URL of the raw image.")
    cloudinary_public_id: str = Field(..., description="Cloudinary public ID of the raw image.")
    width: int
    height: int
    size_bytes: int


# ── Primary CV Analysis Response ──────────────────────────────────────────────

class CVAnalysisResponse(BaseSchema):
    """
    Full response from POST /api/v1/cv/analyze.

    Contains Cloudinary URLs, damage assessment, heatmap, and itemised repair costs.
    """

    # ── Metadata ──────────────────────────────────────────────
    prediction_id: uuid.UUID
    images_processed: int = Field(
        ..., description="Number of images successfully processed."
    )
    primary_angle: str | None = Field(
        None,
        description="Image angle selected for primary damage analysis.",
    )
    uploaded_images: list[ImageUploadResult] = Field(
        default_factory=list,
        description="Metadata for all successfully uploaded images.",
    )

    # ── Vehicle Identification ─────────────────────────────────
    vehicle_detected: bool = Field(
        ...,
        description="Whether a vehicle was detected in the primary image.",
    )
    vehicle_type: str | None = Field(
        None,
        description="Classified vehicle type (SUV, Sedan, Hatchback, etc.).",
    )

    # ── Damage Summary ─────────────────────────────────────────
    overall_damage_level: str = Field(
        ...,
        description="Aggregate damage severity: None | Minor | Moderate | Severe",
    )
    damaged_parts: list[str] = Field(
        default_factory=list,
        description="Names of body parts with detected damage.",
    )
    part_analyses: list[DamagedPartDetail] = Field(
        default_factory=list,
        description="Detailed per-part damage assessment.",
    )

    # ── Repair Cost ────────────────────────────────────────────
    total_repair_cost_min: int = Field(
        ..., description="Minimum aggregated repair cost estimate in INR."
    )
    total_repair_cost_max: int = Field(
        ..., description="Maximum aggregated repair cost estimate in INR."
    )
    total_repair_cost_estimate: float = Field(
        ...,
        description="Midpoint repair cost estimate in INR (deductible from vehicle price).",
    )

    # ── Heatmap ────────────────────────────────────────────────
    heatmap_url: str | None = Field(
        None,
        description="Permanent Cloudinary URL of the generated damage heatmap overlay.",
    )
    heatmap_public_id: str | None = None

    # ── Technical ─────────────────────────────────────────────
    yolo_used: bool = Field(
        ...,
        description="Whether YOLO was available and used for vehicle detection.",
    )
    processing_notes: list[str] = Field(
        default_factory=list,
        description="Diagnostic messages from the CV pipeline.",
    )
    analysed_at: datetime


# ── Image List Response ────────────────────────────────────────────────────────

class PredictionImageItem(BaseSchema):
    """Summary of a single stored PredictionImage record."""

    id: uuid.UUID
    image_url: str
    heatmap_url: str | None
    cloudinary_public_id: str | None
    image_angle: str
    is_primary: bool
    damage_level: str
    cv_analysis_result: dict | None
    created_at: datetime


class PredictionImagesResponse(BaseSchema):
    """Response for GET /api/v1/cv/{prediction_id}/images."""

    prediction_id: uuid.UUID
    images: list[PredictionImageItem] = []
    total: int
