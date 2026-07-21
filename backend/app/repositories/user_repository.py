"""
AutoWorth AI — User Repository

Data access layer for user operations.
All database queries for users live here — never in services or routes.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by email address."""
        result = await self.db.execute(
            select(User)
            .where(User.email == email.lower())
            .options(selectinload(User.role))
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_role(self, user_id: uuid.UUID) -> User | None:
        """Fetch a user with their role eagerly loaded."""
        result = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.role))
        )
        return result.scalar_one_or_none()

    async def get_by_oauth_sub(self, provider: str, sub: str) -> User | None:
        """Fetch a user by OAuth provider + subject ID."""
        result = await self.db.execute(
            select(User).where(
                User.oauth_provider == provider,
                User.oauth_sub == sub,
            )
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """Check if an email is already registered."""
        result = await self.db.execute(
            select(User.id).where(User.email == email.lower())
        )
        return result.scalar_one_or_none() is not None

    async def get_all_paginated(
        self, *, skip: int = 0, limit: int = 50, active_only: bool = False
    ) -> list[User]:
        """Paginated user list for admin dashboard."""
        query = select(User).options(selectinload(User.role))
        if active_only:
            query = query.where(User.is_active.is_(True))
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
