"""
AutoWorth AI — Variant Model

Lowest level of vehicle taxonomy.
Example: Swift VXI, Swift ZXI, City ZX.
"""

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Variant(Base, TimestampMixin):
    __tablename__ = "variants"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ── Foreign Keys ──────────────────────────────────────────
    car_model_id: Mapped[int] = mapped_column(
        ForeignKey("car_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Relationships ─────────────────────────────────────────
    car_model: Mapped["CarModel"] = relationship(  # noqa: F821
        "CarModel", back_populates="variants"
    )
    vehicles: Mapped[list["Vehicle"]] = relationship(  # noqa: F821
        "Vehicle", back_populates="variant"
    )

    def __repr__(self) -> str:
        return f"<Variant id={self.id} name={self.name!r}>"
