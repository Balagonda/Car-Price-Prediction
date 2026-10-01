import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.services.prediction_service import PredictionService
from app.schemas.prediction import PredictionRequest
import json
import uuid

async def test_predict():
    async with AsyncSessionLocal() as session:
        service = PredictionService(session)
        # Create dummy prediction data
        # From earlier in the chat, the frontend submits snake_case values (from vehicle enums)
        # However, earlier I modified prediction-wizard.tsx to submit literal string formats? Wait, no, I was going to.
        # Let's see what the backend expects in PredictionCreate
        data = PredictionRequest(
            brand_id=1,
            car_model_id=1,
            city_id=1,
            manufacturing_year=2018,
            fuel_type="Petrol",
            transmission="Manual",
            owner_type="First Owner",
            kilometers_driven=45000,
            seller_type="Individual",
            engine_cc=1497,
            mileage_kmpl=17.4,
            max_power_bhp=117.6,
            seats=5,
            category="Sedan",
            insurance_status="Comprehensive"
        )
        try:
            # Need a UUID for the user
            user_id = uuid.uuid4()
            res = await service.create_prediction(user_id=user_id, data=data)
            print(json.dumps(res.model_dump(), indent=2, default=str))
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_predict())
