"""
AutoWorth AI — Dataset Model

Tracks CSV datasets uploaded by admins.
Each ModelVersion can be linked to the dataset it was trained on.
"""

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Dataset(Base, TimestampMixin):
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)   # e.g. "v3"
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── File Metadata ─────────────────────────────────────────
    file_url: Mapped[str | None] = mapped_column(Text, nullable=True)  # Cloudinary URL
    original_filename: Mapped[str | None] = mapped_column(String(500), nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Validation Results ────────────────────────────────────
    duplicate_rows_removed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    invalid_rows_removed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # ── Uploader ──────────────────────────────────────────────
    uploaded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Relationships ─────────────────────────────────────────
    model_versions: Mapped[list["ModelVersion"]] = relationship(  # noqa: F821
        "ModelVersion", back_populates="dataset"
    )

    def __repr__(self) -> str:
        return f"<Dataset id={self.id} name={self.name!r} version={self.version!r}>"
