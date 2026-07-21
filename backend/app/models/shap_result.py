"""
AutoWorth AI — ShapResult Model

Stores per-feature SHAP contributions for each prediction.
Enables the Explainable AI panel on the frontend.
"""

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ShapResult(Base):
    __tablename__ = "shap_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ── SHAP Data ─────────────────────────────────────────────
    feature_name: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    shap_value: Mapped[float] = mapped_column(Float, nullable=False)
    impact_direction: Mapped[str] = mapped_column(
        String(10), nullable=False  # "positive" | "negative"
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)  # Display order (1 = top)
    human_readable_impact: Mapped[str | None] = mapped_column(
        String(500), nullable=True
        # e.g. "Mileage reduced vehicle value by ₹35,000"
    )

    # ── Foreign Keys ──────────────────────────────────────────
    prediction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("predictions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Relationships ─────────────────────────────────────────
    prediction: Mapped["Prediction"] = relationship(  # noqa: F821
        "Prediction", back_populates="shap_results"
    )

    def __repr__(self) -> str:
        return (
            f"<ShapResult feature={self.feature_name!r} "
            f"value={self.shap_value:.4f} "
            f"direction={self.impact_direction}>"
        )
