"""
AutoWorth AI — Base Repository

Generic async CRUD operations shared by all repositories.
Repositories are the ONLY layer that interacts with SQLAlchemy sessions.
"""

from typing import Any, Generic, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository providing basic CRUD operations.

    Usage:
        class UserRepository(BaseRepository[User]):
            def __init__(self, db: AsyncSession):
                super().__init__(User, db)
    """

    def __init__(self, model: Type[ModelType], db: AsyncSession) -> None:
        self.model = model
        self.db = db

    async def get_by_id(self, record_id: Any) -> ModelType | None:
        """Fetch a single record by primary key."""
        return await self.db.get(self.model, record_id)

    async def get_all(self, *, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """Fetch a paginated list of all records."""
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> ModelType:
        """Create and persist a new record."""
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()  # Assign DB-generated values (id, timestamps)
        await self.db.refresh(instance)
        return instance

    async def update(self, instance: ModelType, **kwargs: Any) -> ModelType:
        """Update attributes on an existing record."""
        for key, value in kwargs.items():
            setattr(instance, key, value)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> None:
        """Delete a record from the database."""
        await self.db.delete(instance)
        await self.db.flush()

    async def count(self) -> int:
        """Return the total number of records."""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one()
