"""
AutoWorth AI — ActivityLog Repository

Handles database operations for ActivityLogs.
"""

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog
from app.repositories.base import BaseRepository


class ActivityLogRepository(BaseRepository[ActivityLog]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(ActivityLog, db)

    async def get_recent_activities(self, limit: int = 50) -> Sequence[ActivityLog]:
        """Fetch the most recent activities."""
        result = await self.db.execute(
            select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(limit)
        )
        return result.scalars().all()
