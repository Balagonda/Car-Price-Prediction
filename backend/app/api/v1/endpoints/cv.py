"""
AutoWorth AI — CV Endpoints (Phase 4)

Provides:
  POST /api/v1/cv/analyze       — Upload vehicle images & run damage analysis
  GET  /api/v1/cv/{id}/images   — List all stored images for a prediction

Layer: API Layer
Auth: VerifiedUser (JWT)
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status

from app.api.v1.dependencies import DBSession, VerifiedUser
from app.models.prediction_image import ImageAngle
from app.repositories.cv_repository import CVRepository
from app.schemas.common import APIResponse
from app.schemas.cv import (
    CVAnalysisResponse,
    PredictionImageItem,
    PredictionImagesResponse,
)
from app.services.cv_service import CVService, UploadedFile

router = APIRouter(prefix="/cv", tags=["Computer Vision"])

# ── Allowed content types ─────────────────────────────────────────────────────
_ALLOWED_TYPES: frozenset[str] = frozenset(
    {"image/jpeg", "image/jpg", "image/png", "image/webp"}
)


# ─────────────────────────────────────────────────────────────────────────────
# POST /cv/analyze
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/analyze",
    response_model=APIResponse[CVAnalysisResponse],
    status_code=status.HTTP_200_OK,
    summary="Analyze Vehicle Images (YOLO + Damage Detection)",
    description=(
        "Upload one or more vehicle images (Front, Rear, Left Side, Right Side, Interior). "
        "The pipeline detects vehicle presence via YOLOv8, segments body parts, "
        "scores damage via OpenCV edge/texture analysis, generates a damage heatmap, "
        "uploads all assets to Cloudinary, and returns itemised repair cost estimates. "
        "This endpoint is decoupled from the price prediction pipeline — a failure "
        "here does NOT affect the prediction result."
    ),
)
async def analyze_vehicle_images(
    current_user: VerifiedUser,
    db: DBSession,
    # ── Prediction linkage ───────────────────────────────────
    prediction_id: Annotated[
        uuid.UUID,
        Form(description="UUID of an existing prediction to attach images to."),
    ],
    # ── Image uploads (all optional; at least one required) ──
    front_image: Annotated[
        UploadFile | None,
        File(description="Front view of the vehicle."),
    ] = None,
    rear_image: Annotated[
        UploadFile | None,
        File(description="Rear view of the vehicle."),
    ] = None,
    left_image: Annotated[
        UploadFile | None,
        File(description="Left side view of the vehicle."),
    ] = None,
    right_image: Annotated[
        UploadFile | None,
        File(description="Right side view of the vehicle."),
    ] = None,
    interior_image: Annotated[
        UploadFile | None,
        File(description="Interior / cabin view."),
    ] = None,
) -> APIResponse[CVAnalysisResponse]:
    """
    Upload vehicle images and receive a full AI damage analysis report.

    ### Processing Order
    1. Validate MIME type for all uploaded files.
    2. Upload raw images to Cloudinary (`autoworth/raw/{prediction_id}/`).
    3. Select best angle: Front > Left > Right > Rear > Interior.
    4. Run YOLOv8 detection + OpenCV damage scoring on primary image.
    5. Generate heatmap overlay → upload to Cloudinary (`autoworth/heatmaps/`).
    6. Persist results and update `Prediction.cv_*` summary fields.

    ### Constraints
    - At least **one** image must be provided.
    - Each image must be ≤ 10 MB, ≥ 300×300 px, aspect ratio 0.5–3.0.
    - Total processing budget: **5 seconds** (configurable via `CV_TIMEOUT_SECONDS`).
    """
    # ── Build file list ────────────────────────────────────────────────────────
    angle_file_pairs: list[tuple[ImageAngle, UploadFile]] = [
        (ImageAngle.FRONT,    front_image),
        (ImageAngle.REAR,     rear_image),
        (ImageAngle.LEFT,     left_image),
        (ImageAngle.RIGHT,    right_image),
        (ImageAngle.INTERIOR, interior_image),
    ]

    uploaded_files: list[UploadedFile] = []

    for angle, upload_file in angle_file_pairs:
        if upload_file is None:
            continue

        # MIME type pre-check before reading full bytes
        content_type = (upload_file.content_type or "").lower().strip()
        if content_type not in _ALLOWED_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "success": False,
                    "message": (
                        f"File '{upload_file.filename}' has unsupported type "
                        f"'{upload_file.content_type}'. Accepted: JPEG, PNG, WebP."
                    ),
                    "error_code": "INVALID_IMAGE_TYPE",
                },
            )

        file_bytes = await upload_file.read()

        uploaded_files.append(
            UploadedFile(
                filename=upload_file.filename or f"{angle.value}.jpg",
                content_type=content_type,
                file_bytes=file_bytes,
                angle=angle,
            )
        )

    if not uploaded_files:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "success": False,
                "message": (
                    "No image files were provided. Please upload at least one vehicle image "
                    "(front_image, rear_image, left_image, right_image, or interior_image)."
                ),
                "error_code": "NO_IMAGES_PROVIDED",
            },
        )

    # ── Run CV pipeline ────────────────────────────────────────────────────────
    service = CVService(db)
    result = await service.analyze_prediction_images(
        prediction_id=prediction_id,
        files=uploaded_files,
        owner_user_id=current_user.id,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "success": False,
                "message": result.error or "CV analysis failed.",
                "error_code": "CV_ANALYSIS_FAILED",
            },
        )

    return APIResponse(
        success=True,
        message=(
            f"Vehicle image analysis complete. "
            f"Damage level: {result.response.overall_damage_level}. "
            f"Estimated repair cost: ₹{result.response.total_repair_cost_estimate:,.0f}."
        ),
        data=result.response,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /cv/{prediction_id}/images
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/{prediction_id}/images",
    response_model=APIResponse[PredictionImagesResponse],
    summary="Get Prediction Images",
    description=(
        "Retrieve all stored vehicle images and CV analysis results "
        "for a given prediction."
    ),
)
async def get_prediction_images(
    prediction_id: uuid.UUID,
    current_user: VerifiedUser,
    db: DBSession,
) -> APIResponse[PredictionImagesResponse]:
    """
    Fetch all PredictionImage records attached to a prediction.

    Returns Cloudinary URLs, damage levels, heatmap URLs, and raw CV JSON
    for each stored image.
    """
    cv_repo = CVRepository(db)
    images = await cv_repo.get_images_for_prediction(prediction_id)

    image_items = [
        PredictionImageItem(
            id=img.id,
            image_url=img.image_url,
            heatmap_url=img.heatmap_url,
            cloudinary_public_id=img.cloudinary_public_id,
            image_angle=img.image_angle.value,
            is_primary=img.is_primary,
            damage_level=img.damage_level.value,
            cv_analysis_result=img.cv_analysis_result,
            created_at=img.created_at,
        )
        for img in images
    ]

    return APIResponse(
        success=True,
        message=f"Retrieved {len(image_items)} image(s) for prediction {prediction_id}.",
        data=PredictionImagesResponse(
            prediction_id=prediction_id,
            images=image_items,
            total=len(image_items),
        ),
    )
