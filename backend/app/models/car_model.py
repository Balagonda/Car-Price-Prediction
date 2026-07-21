"""
AutoWorth AI — CarModel Model

Mid-level vehicle taxonomy.
Example: Swift, City, Creta, Nexon.
Named CarModel to avoid conflict with SQLAlchemy's own Model class.
"""

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class CarModel(Base, TimestampMixin):
    __tablename__ = "car_models"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ── Foreign Keys ──────────────────────────────────────────
    brand_id: Mapped[int] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Relationships ─────────────────────────────────────────
    brand: Mapped["Brand"] = relationship("Brand", back_populates="car_models")  # noqa: F821
    variants: Mapped[list["Variant"]] = relationship(  # noqa: F821
        "Variant", back_populates="car_model", cascade="all, delete-orphan"
    )
    vehicles: Mapped[list["Vehicle"]] = relationship(  # noqa: F821
        "Vehicle", back_populates="car_model"
    )

    def __repr__(self) -> str:
        return f"<CarModel id={self.id} name={self.name!r} brand_id={self.brand_id}>"
