"""
AutoWorth AI — Recommendation Model

AI-generated recommendations attached to each prediction.
E.g., "Consider servicing the engine before selling to increase resale value."
"""

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class RecommendationPriority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[RecommendationPriority] = mapped_column(
        Enum(RecommendationPriority, name="recommendation_priority_enum"),
        default=RecommendationPriority.MEDIUM,
        nullable=False,
    )
    display_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # ── Foreign Keys ──────────────────────────────────────────
    prediction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("predictions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Relationships ─────────────────────────────────────────
    prediction: Mapped["Prediction"] = relationship(  # noqa: F821
        "Prediction", back_populates="recommendations"
    )

    def __repr__(self) -> str:
        return f"<Recommendation id={self.id} title={self.title!r} priority={self.priority}>"
