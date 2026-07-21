"""
AutoWorth AI — ActivityLog Model

Structured audit trail for all user actions.
Used by admin analytics and live activity feed.
"""

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ActionType(str, enum.Enum):
    REGISTER = "register"
    LOGIN = "login"
    LOGOUT = "logout"
    PASSWORD_RESET = "password_reset"
    PREDICTION_CREATED = "prediction_created"
    PDF_DOWNLOADED = "pdf_downloaded"
    IMAGE_UPLOADED = "image_uploaded"
    FAVORITE_ADDED = "favorite_added"
    FAVORITE_REMOVED = "favorite_removed"
    DATASET_UPLOADED = "dataset_uploaded"
    MODEL_TRAINED = "model_trained"
    MODEL_ACTIVATED = "model_activated"
    USER_DEACTIVATED = "user_deactivated"
    USER_PROMOTED = "user_promoted"
    FEEDBACK_SUBMITTED = "feedback_submitted"


class ActivityLog(Base, TimestampMixin):
    __tablename__ = "activity_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    action: Mapped[ActionType] = mapped_column(
        Enum(ActionType, name="action_type_enum"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True  # e.g. "prediction", "dataset"
    )
    entity_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True  # UUID or int as string
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    extra_data: Mapped[str | None] = mapped_column(
        Text, nullable=True  # Additional JSON context (replaces 'metadata' — reserved by SQLAlchemy)
    )

    # ── Foreign Keys ──────────────────────────────────────────
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Relationships ─────────────────────────────────────────
    user: Mapped["User | None"] = relationship(  # noqa: F821
        "User", back_populates="activity_logs"
    )

    def __repr__(self) -> str:
        return f"<ActivityLog action={self.action} user_id={self.user_id}>"
