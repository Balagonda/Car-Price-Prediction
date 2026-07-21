"""
AutoWorth AI — Session Repository

Data access layer for UserSession operations.
Handles single-session enforcement by invalidating all prior sessions on login.
"""

import hashlib
import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import UserSession
from app.repositories.base import BaseRepository


class SessionRepository(BaseRepository[UserSession]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(UserSession, db)

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────
    @staticmethod
    def hash_token(token: str) -> str:
        """SHA-256 hash of a JWT string for safe DB storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    # ──────────────────────────────────────────────
    # Write Operations
    # ──────────────────────────────────────────────
    async def create_session(
        self,
        *,
        user_id: uuid.UUID,
        jwt_token_hash: str,
        expires_at: datetime,
        device_info: str | None = None,
        ip_address: str | None = None,
    ) -> UserSession:
        """Persist a new active session record."""
        return await self.create(
            user_id=user_id,
            jwt_token_hash=jwt_token_hash,
            expires_at=expires_at,
            device_info=device_info,
            ip_address=ip_address,
            is_active=True,
        )

    async def invalidate_all_user_sessions(self, user_id: uuid.UUID) -> None:
        """
        Deactivate ALL active sessions for a user.
        Called before issuing a new session to enforce single-session policy.
        """
        await self.db.execute(
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.is_active.is_(True))
            .values(is_active=False)
        )

    async def invalidate_session_by_hash(self, token_hash: str) -> bool:
        """
        Deactivate a specific session by token hash.
        Returns True if a session was found and deactivated, False otherwise.
        """
        result = await self.db.execute(
            select(UserSession).where(
                UserSession.jwt_token_hash == token_hash,
                UserSession.is_active.is_(True),
            )
        )
        session = result.scalar_one_or_none()
        if session:
            await self.update(session, is_active=False)
            return True
        return False

    # ──────────────────────────────────────────────
    # Read Operations
    # ──────────────────────────────────────────────
    async def get_active_session_by_hash(self, token_hash: str) -> UserSession | None:
        """Fetch an active session by its token hash."""
        result = await self.db.execute(
            select(UserSession).where(
                UserSession.jwt_token_hash == token_hash,
                UserSession.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_user_active_sessions(self, user_id: uuid.UUID) -> list[UserSession]:
        """Return all active sessions for a user (for admin tooling)."""
        result = await self.db.execute(
            select(UserSession).where(
                UserSession.user_id == user_id,
                UserSession.is_active.is_(True),
            )
        )
        return list(result.scalars().all())
