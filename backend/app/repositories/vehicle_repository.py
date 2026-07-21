"""
AutoWorth AI — Vehicle Repository

Data access layer for Vehicle records and their price history.
Used by PredictionService to create input vehicles and by MLService
for building the KNN similarity pool.

Layer: Repository Layer
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.brand import Brand
from app.models.car_model import CarModel
from app.models.city import City
from app.models.prediction import Prediction
from app.models.vehicle import Vehicle
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class VehicleRepository(BaseRepository[Vehicle]):
    """Repository for Vehicle catalog CRUD and history queries."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Vehicle, db)

    # ──────────────────────────────────────────────
    # Taxonomy Lookups (FK Resolution)
    # ──────────────────────────────────────────────
    async def get_brand_name(self, brand_id: int) -> str:
        """Return the brand name for a given brand_id, or 'Unknown'."""
        result = await self.db.execute(
            select(Brand.name).where(Brand.id == brand_id)
        )
        name = result.scalar_one_or_none()
        return str(name) if name else "Unknown"

    async def get_model_name(self, car_model_id: int) -> str:
        """Return the car model name for a given car_model_id, or 'Unknown'."""
        result = await self.db.execute(
            select(CarModel.name).where(CarModel.id == car_model_id)
        )
        name = result.scalar_one_or_none()
        return str(name) if name else "Unknown"

    async def get_city_name(self, city_id: int | None) -> str:
        """Return the city name for a given city_id, or 'Unknown'."""
        if city_id is None:
            return "Unknown"
        result = await self.db.execute(
            select(City.name).where(City.id == city_id)
        )
        name = result.scalar_one_or_none()
        return str(name) if name else "Unknown"

    # ──────────────────────────────────────────────
    # Vehicle Creation
    # ──────────────────────────────────────────────
    async def create_vehicle(self, **kwargs: Any) -> Vehicle:
        """
        Create and flush a new Vehicle record.

        Accepts all keyword arguments matching Vehicle column names.
        Returns the flushed (not yet committed) Vehicle instance.
        """
        return await self.create(**kwargs)

    # ──────────────────────────────────────────────
    # Historical Vehicles for KNN Pool
    # ──────────────────────────────────────────────
    async def get_historical_vehicles(
        self, limit: int = 5000
    ) -> list[dict[str, Any]]:
        """
        Fetch historical vehicles with their completed prediction prices.

        Used to build the KNN similarity index at training time.
        Returns a list of dicts suitable for MLPipeline._build_knn_index().
        """
        result = await self.db.execute(
            select(Vehicle, Prediction.estimated_price)
            .join(Prediction, Prediction.vehicle_id == Vehicle.id, isouter=True)
            .options(
                selectinload(Vehicle.brand),
                selectinload(Vehicle.car_model),
                selectinload(Vehicle.city),
            )
            .where(Prediction.estimated_price.isnot(None))
            .order_by(Vehicle.id.desc())
            .limit(limit)
        )

        records: list[dict[str, Any]] = []
        for vehicle, price in result.all():
            brand_name = vehicle.brand.name if vehicle.brand else "Unknown"
            model_name = vehicle.car_model.name if vehicle.car_model else "Unknown"
            city_name = vehicle.city.name if vehicle.city else "Unknown"

            records.append({
                "brand": brand_name,
                "model": model_name,
                "manufacturing_year": vehicle.manufacturing_year,
                "fuel_type": vehicle.fuel_type.value if vehicle.fuel_type else "Petrol",
                "transmission": (
                    vehicle.transmission.value if vehicle.transmission else "Manual"
                ),
                "owner_type": (
                    vehicle.owner_type.value if vehicle.owner_type else "First Owner"
                ),
                "seller_type": (
                    vehicle.seller_type.value if vehicle.seller_type else "Individual"
                ),
                "category": (
                    vehicle.category.value if vehicle.category else "Unknown"
                ),
                "city": city_name,
                "kilometers_driven": vehicle.kilometers_driven,
                "engine_cc": vehicle.engine_cc or 1200,
                "mileage_kmpl": vehicle.mileage_kmpl or 15.0,
                "max_power_bhp": vehicle.max_power_bhp or 80.0,
                "seats": vehicle.seats or 5,
                "selling_price": float(price) if price else 0.0,
            })

        logger.info(
            "📊 [VehicleRepository] Fetched %d historical vehicles for KNN pool",
            len(records),
        )
        return records
