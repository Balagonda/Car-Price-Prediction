"""
AutoWorth AI — Prediction Model

Core prediction record.
UUID PK used for prediction IDs shown to users and in PDF reports.
SHAP values and similar vehicles stored as JSONB for flexibility.
"""

import enum
import uuid

from sqlalchemy import Enum, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class FairPriceStatus(str, enum.Enum):
    BELOW_MARKET = "Below Market"
    FAIR = "Fair"
    ABOVE_MARKET = "Above Market"


class Prediction(Base, TimestampMixin):
    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # ── ML Outputs ────────────────────────────────────────────
    estimated_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0–1.0
    price_range_min: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    price_range_max: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    fair_price_status: Mapped[FairPriceStatus] = mapped_column(
        Enum(FairPriceStatus, name="fair_price_status_enum"), nullable=False
    )
    depreciation_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    showroom_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    # ── SHAP & Explanations (stored as JSONB) ─────────────────
    shap_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    similar_vehicles: Mapped[list | None] = mapped_column(JSON, nullable=True)  # 5 records

    # ── Computer Vision Summary ───────────────────────────────
    cv_damage_detected: Mapped[bool | None] = mapped_column(default=False, nullable=True)
    cv_damage_severity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cv_repair_cost_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Status ────────────────────────────────────────────────
    is_pdf_generated: Mapped[bool] = mapped_column(default=False, nullable=False)
    pdf_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Foreign Keys ──────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    model_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("model_versions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Relationships ─────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="predictions")  # noqa: F821
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="predictions")  # noqa: F821
    model_version: Mapped["ModelVersion | None"] = relationship(  # noqa: F821
        "ModelVersion", back_populates="predictions"
    )
    images: Mapped[list["PredictionImage"]] = relationship(  # noqa: F821
        "PredictionImage", back_populates="prediction", cascade="all, delete-orphan"
    )
    shap_results: Mapped[list["ShapResult"]] = relationship(  # noqa: F821
        "ShapResult", back_populates="prediction", cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(  # noqa: F821
        "Recommendation", back_populates="prediction", cascade="all, delete-orphan"
    )
    favorites: Mapped[list["Favorite"]] = relationship(  # noqa: F821
        "Favorite", back_populates="prediction", cascade="all, delete-orphan"
    )
    feedback: Mapped[list["Feedback"]] = relationship(  # noqa: F821
        "Feedback", back_populates="prediction", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Prediction id={self.id} "
            f"price={self.estimated_price} "
            f"confidence={self.confidence_score:.2f}>"
        )
