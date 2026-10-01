import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.database import AsyncSessionLocal
from app.services.ml_service import MLService
from app.repositories.ml_model_repository import MLModelRepository
from pathlib import Path
import uuid

async def train_and_activate():
    print("Starting ML Model Training Script...")
    async with AsyncSessionLocal() as session:
        print("Connected to DB. Initializing ML Service...")
        service = MLService()
        
        # 1. Train model
        print("Training model... This may take a minute or two (Optuna tuning).")
        try:
            result = await service.run_training(
                dataset_path=Path("../Docs/cars_24_combined.csv"), 
                version_tag="v_manual_1",
                db=session
            )
            print(f"Training completed successfully! Status: {result['status']}")
            
            # 2. Activate it
            print("Activating the new model version...")
            model_repo = MLModelRepository(session)
            models = await model_repo.get_all_models()
            if not models:
                print("Error: No models found in the database.")
                return
                
            main_model = models[0]
            latest_version = main_model.versions[-1]
            
            await model_repo.activate_version(latest_version.id)
            await session.commit()
            print(f"Activated model version {latest_version.version_tag} successfully!")
            print("You can now go back to the Valuation page and predict prices!")
            
        except Exception as e:
            print(f"Failed to train model: {e}")

if __name__ == "__main__":
    asyncio.run(train_and_activate())
