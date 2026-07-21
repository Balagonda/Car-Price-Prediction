"""
AutoWorth AI — CV Repository (Phase 4)

Database operations for PredictionImage records and CV summary updates on Prediction.

Layer: Repository Layer
"""

from __future__ import annotations

import uuid
import logging
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import Prediction
from app.models.prediction_image import DamageLevel, ImageAngle, PredictionImage

logger = logging.getLogger(__name__)


class CVRepository:
    """
    Handles all CV-related DB operations.

    Responsibilities:
    - Persisting PredictionImage rows (URLs, angle, CV results)
    - Updating the CV summary columns on the parent Prediction
    - Fetching image records for a prediction
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Write Operations ───────────────────────────────────────────────────────

    async def save_prediction_image(
        self,
        *,
        prediction_id: uuid.UUID,
        image_url: str,
        cloudinary_public_id: str,
        image_angle: ImageAngle,
        is_primary: bool = False,
        heatmap_url: str | None = None,
        damage_level: DamageLevel = DamageLevel.NONE,
        cv_analysis_result: dict[str, Any] | None = None,
    ) -> PredictionImage:
        """
        Persist a new PredictionImage record.

        Args:
            prediction_id: FK to the parent Prediction.
            image_url: Secure Cloudinary URL of the raw image.
            cloudinary_public_id: Cloudinary public_id for future operations.
            image_angle: Enum angle value.
            is_primary: Whether this image was the primary analysis image.
            heatmap_url: Cloudinary URL of the generated heatmap (if any).
            damage_level: Aggregated DamageLevel enum value.
            cv_analysis_result: Full JSON CV result dict.

        Returns:
            Persisted PredictionImage ORM object (flushed, not yet committed).
        """
        record = PredictionImage(
            prediction_id=prediction_id,
            image_url=image_url,
            cloudinary_public_id=cloudinary_public_id,
            image_angle=image_angle,
            is_primary=is_primary,
            heatmap_url=heatmap_url,
            damage_level=damage_level,
            cv_analysis_result=cv_analysis_result,
        )
        self._db.add(record)
        await self._db.flush()

        logger.debug(
            "💾 [CVRepository] Saved PredictionImage id=%s angle=%s primary=%s",
            record.id,
            image_angle.value,
            is_primary,
        )
        return record

    async def update_prediction_cv_summary(
        self,
        *,
        prediction_id: uuid.UUID,
        cv_damage_detected: bool,
        cv_damage_severity: str,
        cv_repair_cost_estimate: float,
    ) -> None:
        """
        Update the CV summary columns on the parent Prediction record.

        Uses a direct UPDATE statement to avoid a SELECT + ORM merge,
        which is more efficient when the Prediction is not already in session.
        """
        stmt = (
            update(Prediction)
            .where(Prediction.id == prediction_id)
            .values(
                cv_damage_detected=cv_damage_detected,
                cv_damage_severity=cv_damage_severity,
                cv_repair_cost_estimate=cv_repair_cost_estimate,
            )
        )
        await self._db.execute(stmt)

        logger.debug(
            "💾 [CVRepository] Updated Prediction %s CV summary — "
            "damage=%s severity=%s cost=₹%.0f",
            prediction_id,
            cv_damage_detected,
            cv_damage_severity,
            cv_repair_cost_estimate,
        )

    # ── Read Operations ────────────────────────────────────────────────────────

    async def get_images_for_prediction(
        self,
        prediction_id: uuid.UUID,
    ) -> list[PredictionImage]:
        """
        Retrieve all PredictionImage records for a given prediction,
        ordered by is_primary DESC, then creation time ASC.
        """
        stmt = (
            select(PredictionImage)
            .where(PredictionImage.prediction_id == prediction_id)
            .order_by(
                PredictionImage.is_primary.desc(),
                PredictionImage.created_at.asc(),
            )
        )
        result = await self._db.execute(stmt)
        images = list(result.scalars().all())

        logger.debug(
            "🔍 [CVRepository] Fetched %d images for prediction %s",
            len(images),
            prediction_id,
        )
        return images

    async def get_primary_image(
        self,
        prediction_id: uuid.UUID,
    ) -> PredictionImage | None:
        """Return the primary PredictionImage for a prediction, or None."""
        stmt = (
            select(PredictionImage)
            .where(
                PredictionImage.prediction_id == prediction_id,
                PredictionImage.is_primary.is_(True),
            )
            .limit(1)
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()
