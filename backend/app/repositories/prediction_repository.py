"""
AutoWorth AI — Prediction Repository

Data access layer for prediction and related sub-entity operations.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.prediction import Prediction
from app.repositories.base import BaseRepository


class PredictionRepository(BaseRepository[Prediction]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Prediction, db)

    async def get_by_user(
        self,
        user_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Prediction]:
        """Fetch a user's prediction history, newest first."""
        result = await self.db.execute(
            select(Prediction)
            .where(Prediction.user_id == user_id)
            .options(
                selectinload(Prediction.vehicle),
                selectinload(Prediction.images),
                selectinload(Prediction.shap_results),
                selectinload(Prediction.recommendations),
            )
            .order_by(Prediction.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_with_full_details(
        self, prediction_id: uuid.UUID
    ) -> Prediction | None:
        """Fetch a single prediction with all related data."""
        result = await self.db.execute(
            select(Prediction)
            .where(Prediction.id == prediction_id)
            .options(
                selectinload(Prediction.user),
                selectinload(Prediction.vehicle),
                selectinload(Prediction.model_version),
                selectinload(Prediction.images),
                selectinload(Prediction.shap_results),
                selectinload(Prediction.recommendations),
            )
        )
        return result.scalar_one_or_none()

    async def count_by_user(self, user_id: uuid.UUID) -> int:
        """Total predictions count for a user."""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count()).select_from(Prediction).where(
                Prediction.user_id == user_id
            )
        )
        return result.scalar_one()
