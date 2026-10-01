from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.v1.dependencies import DBSession
from app.models.brand import Brand
from app.models.car_model import CarModel
from app.models.variant import Variant
from app.models.city import City
from app.schemas.vehicle import BrandResponse, CarModelResponse, VariantResponse, CityResponse
from app.schemas.common import APIResponse

router = APIRouter(prefix="/vehicles", tags=["vehicles"])

@router.get("/brands", response_model=APIResponse[list[BrandResponse]])
async def get_brands(db: DBSession):
    result = await db.execute(select(Brand).where(Brand.is_active == True).order_by(Brand.name))
    brands = result.scalars().all()
    return APIResponse(success=True, message="Brands retrieved", data=brands)

@router.get("/brands/{brand_id}/models", response_model=APIResponse[list[CarModelResponse]])
async def get_models_by_brand(brand_id: int, db: DBSession):
    result = await db.execute(
        select(CarModel)
        .where(CarModel.brand_id == brand_id, CarModel.is_active == True)
        .order_by(CarModel.name)
    )
    models = result.scalars().all()
    return APIResponse(success=True, message="Models retrieved", data=models)

@router.get("/models/{model_id}/variants", response_model=APIResponse[list[VariantResponse]])
async def get_variants_by_model(model_id: int, db: DBSession):
    result = await db.execute(
        select(Variant)
        .where(Variant.car_model_id == model_id, Variant.is_active == True)
        .order_by(Variant.name)
    )
    variants = result.scalars().all()
    return APIResponse(success=True, message="Variants retrieved", data=variants)

@router.get("/cities", response_model=APIResponse[list[CityResponse]])
async def get_cities(db: DBSession):
    result = await db.execute(select(City).where(City.is_active == True).order_by(City.name))
    cities = result.scalars().all()
    return APIResponse(success=True, message="Cities retrieved", data=cities)
