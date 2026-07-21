"""
AutoWorth AI — Vehicle Model

The vehicle catalog — all enumerated specs used for ML prediction input.
Each prediction references a Vehicle record for reproducible history.
"""

import enum

from sqlalchemy import Enum, Float, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class FuelType(str, enum.Enum):
    PETROL = "Petrol"
    DIESEL = "Diesel"
    CNG = "CNG"
    LPG = "LPG"
    ELECTRIC = "Electric"
    HYBRID = "Hybrid"


class TransmissionType(str, enum.Enum):
    MANUAL = "Manual"
    AUTOMATIC = "Automatic"
    AMT = "AMT"
    DCT = "DCT"
    CVT = "CVT"


class OwnerType(str, enum.Enum):
    FIRST = "First Owner"
    SECOND = "Second Owner"
    THIRD = "Third Owner"
    FOURTH_OR_MORE = "Fourth & Above Owner"
    TEST_DRIVE = "Test Drive Car"


class SellerType(str, enum.Enum):
    INDIVIDUAL = "Individual"
    DEALER = "Dealer"
    TRUSTMARK_DEALER = "Trustmark Dealer"


class VehicleCategory(str, enum.Enum):
    HATCHBACK = "Hatchback"
    SEDAN = "Sedan"
    SUV = "SUV"
    MUV = "MUV"
    LUXURY = "Luxury"
    ELECTRIC = "Electric"
    COMMERCIAL = "Commercial"
    COUPE = "Coupe"
    CONVERTIBLE = "Convertible"


class InsuranceStatus(str, enum.Enum):
    COMPREHENSIVE = "Comprehensive"
    THIRD_PARTY = "Third Party"
    ZERO_DEPRECIATION = "Zero Depreciation"
    EXPIRED = "Expired"
    NOT_AVAILABLE = "Not Available"


class Vehicle(Base, TimestampMixin):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ── Taxonomy FKs ──────────────────────────────────────────
    brand_id: Mapped[int] = mapped_column(
        ForeignKey("brands.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    car_model_id: Mapped[int] = mapped_column(
        ForeignKey("car_models.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("variants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    city_id: Mapped[int | None] = mapped_column(
        ForeignKey("cities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Core Specs ────────────────────────────────────────────
    manufacturing_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    fuel_type: Mapped[FuelType] = mapped_column(
        Enum(FuelType, name="fuel_type_enum"), nullable=False, index=True
    )
    transmission: Mapped[TransmissionType] = mapped_column(
        Enum(TransmissionType, name="transmission_type_enum"), nullable=False
    )
    owner_type: Mapped[OwnerType] = mapped_column(
        Enum(OwnerType, name="owner_type_enum"), nullable=False
    )
    seller_type: Mapped[SellerType] = mapped_column(
        Enum(SellerType, name="seller_type_enum"), nullable=False
    )
    category: Mapped[VehicleCategory] = mapped_column(
        Enum(VehicleCategory, name="vehicle_category_enum"), nullable=False, index=True
    )

    # ── Numeric Specs ─────────────────────────────────────────
    kilometers_driven: Mapped[int] = mapped_column(Integer, nullable=False)
    engine_cc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mileage_kmpl: Mapped[float | None] = mapped_column(Float, nullable=True)
    seats: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_power_bhp: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Condition ─────────────────────────────────────────────
    insurance_status: Mapped[InsuranceStatus] = mapped_column(
        Enum(InsuranceStatus, name="insurance_status_enum"), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────
    brand: Mapped["Brand"] = relationship("Brand")  # noqa: F821
    car_model: Mapped["CarModel"] = relationship("CarModel", back_populates="vehicles")  # noqa: F821
    variant: Mapped["Variant | None"] = relationship(  # noqa: F821
        "Variant", back_populates="vehicles"
    )
    city: Mapped["City | None"] = relationship("City", back_populates="vehicles")  # noqa: F821
    predictions: Mapped[list["Prediction"]] = relationship(  # noqa: F821
        "Prediction", back_populates="vehicle"
    )

    def __repr__(self) -> str:
        return (
            f"<Vehicle id={self.id} "
            f"brand_id={self.brand_id} "
            f"year={self.manufacturing_year}>"
        )
