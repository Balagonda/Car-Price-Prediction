"""
AutoWorth AI — Dataset Repository

Handles database operations for the Dataset model.
"""

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset
from app.repositories.base import BaseRepository


class DatasetRepository(BaseRepository[Dataset]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Dataset, db)

    async def get_all_datasets(self) -> Sequence[Dataset]:
        """Fetch all datasets ordered by creation date (newest first)."""
        result = await self.db.execute(
            select(Dataset).order_by(Dataset.created_at.desc())
        )
        return result.scalars().all()

    async def get_latest_dataset(self) -> Dataset | None:
        """Fetch the most recently uploaded active dataset."""
        result = await self.db.execute(
            select(Dataset)
            .where(Dataset.is_active == True)
            .order_by(Dataset.created_at.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def deactivate_all_datasets(self) -> None:
        """Mark all datasets as inactive (used when replacing datasets)."""
        datasets = await self.get_all_datasets()
        for ds in datasets:
            ds.is_active = False
        self.db.add_all(datasets)
        await self.db.flush()
