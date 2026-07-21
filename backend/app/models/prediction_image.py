"""
AutoWorth AI — PredictionImage Model

Stores Cloudinary URLs for uploaded vehicle images and generated damage heatmaps.
CV analysis results stored as JSONB for flexible schema.
"""

import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ImageAngle(str, enum.Enum):
    FRONT = "Front"
    REAR = "Rear"
    LEFT = "Left Side"
    RIGHT = "Right Side"
    INTERIOR = "Interior"
    OTHER = "Other"


class DamageLevel(str, enum.Enum):
    NONE = "None"
    MINOR = "Minor"
    MODERATE = "Moderate"
    SEVERE = "Severe"


class PredictionImage(Base, TimestampMixin):
    __tablename__ = "prediction_images"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── Cloudinary URLs ───────────────────────────────────────
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    heatmap_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    cloudinary_public_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ── Classification ────────────────────────────────────────
    image_angle: Mapped[ImageAngle] = mapped_column(
        Enum(ImageAngle, name="image_angle_enum"),
        default=ImageAngle.FRONT,
        nullable=False,
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False  # Primary image used for CV analysis
    )

    # ── CV Results ────────────────────────────────────────────
    damage_level: Mapped[DamageLevel] = mapped_column(
        Enum(DamageLevel, name="damage_level_enum"),
        default=DamageLevel.NONE,
        nullable=False,
    )
    cv_analysis_result: Mapped[dict | None] = mapped_column(
        JSON, nullable=True  # Full CV JSON: detected parts, bboxes, severity
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
        "Prediction", back_populates="images"
    )

    def __repr__(self) -> str:
        return (
            f"<PredictionImage id={self.id} "
            f"angle={self.image_angle} "
            f"damage={self.damage_level}>"
        )
