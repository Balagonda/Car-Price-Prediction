"""
AutoWorth AI — CV Service (Phase 4)

Orchestrates the end-to-end Computer Vision analysis workflow:
  1. Validate each uploaded image file
  2. Upload raw images to Cloudinary
  3. Select the primary image angle for damage analysis
  4. Run CVEngine.analyze() on the primary image
  5. Upload the generated heatmap to Cloudinary
  6. Persist PredictionImage rows and update Prediction CV summary
  7. Return a structured CVAnalysisResult

Design constraints:
  - All I/O inside a single asyncio.wait_for() budget (default 5 s from config).
  - NEVER raises to the API layer — always returns CVServiceResult with success flag.
  - Image upload failures for non-primary images are logged but do not abort.
  - Price prediction pipeline is completely unaffected.

Layer: Service Layer
Dependencies: CVEngine, ImageService, CVRepository
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.ml.cv_engine import CVEngine, CVValidationError
from app.models.prediction_image import DamageLevel, ImageAngle
from app.repositories.cv_repository import CVRepository
from app.schemas.cv import (
    CVAnalysisResponse,
    DamagedPartDetail,
    ImageUploadResult,
)
from app.services.image_service import (
    ImageUploadError,
    ImageValidationError,
    select_primary_angle,
    upload_heatmap,
    upload_raw_image,
    validate_image,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Singleton CV engine — loaded lazily, shared across requests
_cv_engine: CVEngine | None = None


def _get_cv_engine() -> CVEngine:
    global _cv_engine
    if _cv_engine is None:
        _cv_engine = CVEngine(yolo_weights_path=settings.YOLO_MODEL_PATH)
    return _cv_engine


# ── Input / Output Types ──────────────────────────────────────────────────────

@dataclass
class UploadedFile:
    """Represents a single image file ready for processing."""

    filename: str
    content_type: str
    file_bytes: bytes
    angle: ImageAngle


@dataclass
class CVServiceResult:
    """
    Result returned by CVService.analyze_prediction_images().

    Always instantiated (never raises). Check `success` before using data.
    """

    success: bool
    response: CVAnalysisResponse | None = None
    error: str | None = None


# ── CVService ─────────────────────────────────────────────────────────────────

class CVService:
    """
    Orchestrates the full CV pipeline for a prediction's uploaded images.

    Usage:
        service = CVService(db)
        result = await service.analyze_prediction_images(prediction_id, files)
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._cv_repo = CVRepository(db)
        self._engine = _get_cv_engine()

    async def analyze_prediction_images(
        self,
        prediction_id: uuid.UUID,
        files: list[UploadedFile],
        owner_user_id: uuid.UUID | None = None,
    ) -> CVServiceResult:
        """
        Main entry point: validate, upload, analyse, persist, and respond.

        All exceptions are caught; caller always receives a CVServiceResult.
        A 5-second timeout is enforced around the full pipeline.
        """
        try:
            result = await asyncio.wait_for(
                self._run_pipeline(prediction_id, files),
                timeout=float(settings.CV_TIMEOUT_SECONDS),
            )
            return result
        except asyncio.TimeoutError:
            logger.warning(
                "⏱️  [CVService] Analysis timed out after %ds — prediction_id=%s",
                settings.CV_TIMEOUT_SECONDS,
                prediction_id,
            )
            return CVServiceResult(
                success=False,
                error=(
                    f"CV analysis timed out after {settings.CV_TIMEOUT_SECONDS} seconds. "
                    "Price prediction is unaffected. Please try again later."
                ),
            )
        except Exception as exc:
            logger.exception(
                "❌ [CVService] Unexpected error — prediction_id=%s: %s",
                prediction_id,
                exc,
            )
            return CVServiceResult(
                success=False,
                error=f"CV analysis failed due to an internal error: {exc}",
            )

    # ── Pipeline ──────────────────────────────────────────────────────────────

    async def _run_pipeline(
        self,
        prediction_id: uuid.UUID,
        files: list[UploadedFile],
    ) -> CVServiceResult:
        """Full pipeline (runs inside the timeout wrapper)."""

        # ── Step 1: Validate + upload all images ──────────────
        upload_results: list[ImageUploadResult] = []
        available_angles: list[ImageAngle] = []
        file_bytes_by_angle: dict[ImageAngle, bytes] = {}
        validation_metadata: dict[ImageAngle, dict[str, Any]] = {}

        for ufile in files:
            try:
                meta = validate_image(
                    ufile.file_bytes,
                    ufile.content_type,
                    ufile.filename,
                )
            except ImageValidationError as exc:
                logger.warning(
                    "⚠️  [CVService] Validation failed for %s (%s): %s",
                    ufile.filename,
                    ufile.angle.value,
                    exc,
                )
                continue  # Skip invalid images; don't abort

            try:
                upload_info = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda b=ufile.file_bytes, a=ufile.angle: upload_raw_image(
                        b, prediction_id, a, ufile.filename
                    ),
                )
            except ImageUploadError as exc:
                logger.error(
                    "❌ [CVService] Upload failed for %s: %s", ufile.filename, exc
                )
                continue  # Non-fatal for non-primary images

            available_angles.append(ufile.angle)
            file_bytes_by_angle[ufile.angle] = ufile.file_bytes
            validation_metadata[ufile.angle] = meta

            upload_results.append(
                ImageUploadResult(
                    angle=ufile.angle.value,
                    is_primary=False,  # Will be updated after selection
                    cloudinary_url=upload_info["url"],
                    cloudinary_public_id=upload_info["public_id"],
                    width=meta["width"],
                    height=meta["height"],
                    size_bytes=meta["size_bytes"],
                )
            )
            # Persist raw image record (no CV results yet)
            await self._cv_repo.save_prediction_image(
                prediction_id=prediction_id,
                image_url=upload_info["url"],
                cloudinary_public_id=upload_info["public_id"],
                image_angle=ufile.angle,
                is_primary=False,  # Will patch primary below
                damage_level=DamageLevel.NONE,
            )

        if not upload_results:
            return CVServiceResult(
                success=False,
                error="No valid images were successfully uploaded. Please check your files.",
            )

        # ── Step 2: Select primary image ──────────────────────
        primary_angle = select_primary_angle(available_angles)
        if primary_angle is None:
            return CVServiceResult(
                success=False,
                error="Could not determine a primary image for analysis.",
            )

        # Mark the primary image in our response list
        for ur in upload_results:
            if ur.angle == primary_angle.value:
                # Replace is_primary flag (Pydantic model_copy)
                upload_results[upload_results.index(ur)] = ur.model_copy(
                    update={"is_primary": True}
                )
                break

        # ── Step 3: Run CV analysis on primary image ──────────
        primary_bytes = file_bytes_by_angle[primary_angle]
        try:
            cv_result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._engine.analyze(primary_bytes, primary_angle.value),
            )
        except CVValidationError as exc:
            logger.warning("⚠️  [CVService] CV validation error: %s", exc)
            return CVServiceResult(
                success=False,
                error=f"Primary image could not be analysed: {exc}",
            )
        except Exception as exc:
            logger.exception("❌ [CVService] CVEngine.analyze() failed: %s", exc)
            return CVServiceResult(
                success=False,
                error=f"Damage analysis failed: {exc}",
            )

        # ── Step 4: Upload heatmap ─────────────────────────────
        heatmap_url: str | None = None
        heatmap_public_id: str | None = None

        if cv_result.heatmap_bytes:
            try:
                heatmap_info = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: upload_heatmap(cv_result.heatmap_bytes, prediction_id),
                )
                heatmap_url = heatmap_info["url"]
                heatmap_public_id = heatmap_info["public_id"]
            except ImageUploadError as exc:
                logger.warning("⚠️  [CVService] Heatmap upload failed: %s", exc)
                # Non-fatal — analysis result still valid

        # ── Step 5: Persist primary image record with CV data ─
        damage_level_enum = self._map_severity_to_enum(cv_result.overall_severity)

        cv_json: dict[str, Any] = {
            "vehicle_detected": cv_result.vehicle_detected,
            "vehicle_type": cv_result.vehicle_type,
            "overall_severity": cv_result.overall_severity,
            "damaged_parts": cv_result.damaged_parts,
            "part_analyses": [
                {
                    "part_name": p.part_name,
                    "severity": p.severity,
                    "damage_score": p.damage_score,
                    "is_damaged": p.is_damaged,
                    "repair_cost_min": p.repair_cost_min,
                    "repair_cost_max": p.repair_cost_max,
                    "bbox": list(p.bbox),
                }
                for p in cv_result.part_analyses
            ],
            "total_repair_cost_min": cv_result.total_repair_cost_min,
            "total_repair_cost_max": cv_result.total_repair_cost_max,
            "total_repair_cost_estimate": cv_result.total_repair_cost_estimate,
            "heatmap_url": heatmap_url,
            "yolo_available": cv_result.yolo_available,
            "processing_notes": cv_result.processing_notes,
        }

        # Find and update the primary image record
        existing_images = await self._cv_repo.get_images_for_prediction(prediction_id)
        for img in existing_images:
            if img.image_angle == primary_angle:
                img.is_primary = True
                img.heatmap_url = heatmap_url
                img.damage_level = damage_level_enum
                img.cv_analysis_result = cv_json
                self._db.add(img)
                await self._db.flush()
                break

        # ── Step 6: Update Prediction CV summary ──────────────
        await self._cv_repo.update_prediction_cv_summary(
            prediction_id=prediction_id,
            cv_damage_detected=cv_result.vehicle_detected and bool(cv_result.damaged_parts),
            cv_damage_severity=cv_result.overall_severity,
            cv_repair_cost_estimate=cv_result.total_repair_cost_estimate,
        )

        await self._db.commit()

        logger.info(
            "✅ [CVService] Pipeline complete — prediction=%s severity=%s "
            "parts=%d repair=₹%.0f heatmap=%s",
            prediction_id,
            cv_result.overall_severity,
            len(cv_result.damaged_parts),
            cv_result.total_repair_cost_estimate,
            "uploaded" if heatmap_url else "failed",
        )

        # ── Step 7: Build response ─────────────────────────────
        part_details = [
            DamagedPartDetail(
                part_name=p.part_name,
                severity=p.severity,
                damage_score=p.damage_score,
                is_damaged=p.is_damaged,
                repair_cost_min=p.repair_cost_min,
                repair_cost_max=p.repair_cost_max,
                repair_cost_midpoint=(p.repair_cost_min + p.repair_cost_max) / 2.0,
                bbox=list(p.bbox),
            )
            for p in cv_result.part_analyses
        ]

        response = CVAnalysisResponse(
            prediction_id=prediction_id,
            images_processed=len(upload_results),
            primary_angle=primary_angle.value,
            uploaded_images=upload_results,
            vehicle_detected=cv_result.vehicle_detected,
            vehicle_type=cv_result.vehicle_type,
            overall_damage_level=cv_result.overall_severity,
            damaged_parts=cv_result.damaged_parts,
            part_analyses=part_details,
            total_repair_cost_min=cv_result.total_repair_cost_min,
            total_repair_cost_max=cv_result.total_repair_cost_max,
            total_repair_cost_estimate=cv_result.total_repair_cost_estimate,
            heatmap_url=heatmap_url,
            heatmap_public_id=heatmap_public_id,
            yolo_used=cv_result.yolo_available,
            processing_notes=cv_result.processing_notes,
            analysed_at=datetime.now(UTC),
        )

        return CVServiceResult(success=True, response=response)

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _map_severity_to_enum(severity: str) -> DamageLevel:
        """Map a severity string to the DamageLevel DB enum."""
        mapping = {
            "None": DamageLevel.NONE,
            "Minor": DamageLevel.MINOR,
            "Moderate": DamageLevel.MODERATE,
            "Severe": DamageLevel.SEVERE,
        }
        return mapping.get(severity, DamageLevel.NONE)
