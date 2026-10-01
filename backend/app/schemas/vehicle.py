from pydantic import BaseModel

class BrandResponse(BaseModel):
    id: int
    name: str
    logo_url: str | None = None

class CarModelResponse(BaseModel):
    id: int
    name: str
    brand_id: int

class VariantResponse(BaseModel):
    id: int
    name: str
    car_model_id: int

class CityResponse(BaseModel):
    id: int
    name: str
    state: str
