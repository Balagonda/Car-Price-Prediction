"""
AutoWorth AI — ML Model Repository

Data access layer for MLModel and ModelVersion records.
Handles version lifecycle: TRAINING → TRAINED → ACTIVE → ARCHIVED.

Layer: Repository Layer
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ml_model import AlgorithmType, MLModel, ModelStatus, ModelVersion
from app.repositories.base import BaseRepository


class MLModelRepository(BaseRepository[ModelVersion]):
    """Repository for ML model registry and versioning operations."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(ModelVersion, db)

    # ──────────────────────────────────────────────
    # Reads
    # ──────────────────────────────────────────────
    async def get_active_version(self) -> ModelVersion | None:
        """
        Return the single ModelVersion with status='active', or None.

        Includes the parent MLModel for algorithm type lookup.
        """
        result = await self.db.execute(
            select(ModelVersion)
            .where(ModelVersion.status == ModelStatus.ACTIVE)
            .options(selectinload(ModelVersion.ml_model))
            .order_by(ModelVersion.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_all_versions(
        self, *, skip: int = 0, limit: int = 50
    ) -> list[ModelVersion]:
        """Return all ModelVersions with their parent MLModel, newest first."""
        result = await self.db.execute(
            select(ModelVersion)
            .options(selectinload(ModelVersion.ml_model))
            .order_by(ModelVersion.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_version_by_id(
        self, version_id: uuid.UUID
    ) -> ModelVersion | None:
        """Fetch a ModelVersion by UUID, including the parent MLModel."""
        result = await self.db.execute(
            select(ModelVersion)
            .where(ModelVersion.id == version_id)
            .options(selectinload(ModelVersion.ml_model))
        )
        return result.scalar_one_or_none()

    async def get_all_ml_models(self) -> list[MLModel]:
        """Return all MLModel records with their versions."""
        result = await self.db.execute(
            select(MLModel)
            .options(selectinload(MLModel.versions))
            .order_by(MLModel.id)
        )
        return list(result.scalars().all())

    # ──────────────────────────────────────────────
    # Writes
    # ──────────────────────────────────────────────
    async def create_model_and_version(
        self,
        algorithm: AlgorithmType,
        version_tag: str,
        dataset_id: str | None = None,
    ) -> tuple[MLModel, ModelVersion]:
        """
        Create a new MLModel (or reuse an existing one with the same algorithm)
        and attach a new ModelVersion with status=TRAINING.

        Returns:
            (MLModel, ModelVersion) — both flushed but not committed.
        """
        # Find or create the parent MLModel
        result = await self.db.execute(
            select(MLModel).where(MLModel.algorithm == algorithm).limit(1)
        )
        ml_model = result.scalar_one_or_none()

        if ml_model is None:
            ml_model = MLModel(
                name=f"AutoWorth {algorithm.value}",
                algorithm=algorithm,
                description=(
                    f"AutoWorth AI price prediction model using {algorithm.value}."
                ),
            )
            self.db.add(ml_model)
            await self.db.flush()
            await self.db.refresh(ml_model)

        # Create the new version
        model_version = ModelVersion(
            version_tag=version_tag,
            status=ModelStatus.TRAINING,
            ml_model_id=ml_model.id,
            dataset_id=uuid.UUID(dataset_id) if dataset_id else None,
        )
        self.db.add(model_version)
        await self.db.flush()
        await self.db.refresh(model_version)

        return ml_model, model_version

    async def update_version_metrics(
        self,
        version_id: uuid.UUID,
        metrics: dict[str, Any],
    ) -> ModelVersion | None:
        """
        Patch a ModelVersion with training metrics and status.

        Accepted metric keys (all optional):
            r2_score, rmse, mae, cross_val_score, training_time_seconds,
            training_samples, model_artifact_path, preprocessor_path,
            avg_prediction_time_ms, status, notes
        """
        version = await self.get_version_by_id(version_id)
        if version is None:
            return None

        allowed_fields = {
            "r2_score", "rmse", "mae", "cross_val_score",
            "training_time_seconds", "training_samples",
            "model_artifact_path", "preprocessor_path",
            "avg_prediction_time_ms", "status", "notes",
        }
        for field, value in metrics.items():
            if field in allowed_fields:
                setattr(version, field, value)

        self.db.add(version)
        await self.db.flush()
        await self.db.refresh(version)
        return version

    async def activate_version(self, version_id: uuid.UUID) -> ModelVersion:
        """
        Promote a ModelVersion to ACTIVE status.

        Enforces the invariant that only ONE version is ACTIVE at a time:
        all other ACTIVE versions for the same ml_model_id are archived.

        Raises:
            ValueError if the target version is not in TRAINED status.
        """
        version = await self.get_version_by_id(version_id)
        if version is None:
            raise ValueError(f"ModelVersion {version_id} not found.")

        if version.status not in (ModelStatus.TRAINED, ModelStatus.ACTIVE):
            raise ValueError(
                f"Cannot activate version with status={version.status}. "
                "Only TRAINED versions can be activated."
            )

        # Archive any currently ACTIVE versions for the same model
        existing_active_result = await self.db.execute(
            select(ModelVersion).where(
                ModelVersion.ml_model_id == version.ml_model_id,
                ModelVersion.status == ModelStatus.ACTIVE,
                ModelVersion.id != version_id,
            )
        )
        for existing in existing_active_result.scalars().all():
            existing.status = ModelStatus.ARCHIVED
            self.db.add(existing)

        # Activate the target version
        version.status = ModelStatus.ACTIVE
        self.db.add(version)
        await self.db.flush()
        await self.db.refresh(version)
        return version
