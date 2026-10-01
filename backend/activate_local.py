import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.database import AsyncSessionLocal
from app.repositories.ml_model_repository import MLModelRepository

async def activate():
    print("Starting ML Model Activation Script...")
    async with AsyncSessionLocal() as session:
        print("Connected to DB...")
        model_repo = MLModelRepository(session)
        models = await model_repo.get_all_ml_models()
        if not models:
            print("Error: No models found in the database.")
            return
            
        main_model = models[0]
        # Get the latest trained version
        latest_version = None
        for v in main_model.versions:
            if v.status.name == "TRAINED":
                latest_version = v
                
        if not latest_version:
            print("No TRAINED version found to activate.")
            return
            
        print(f"Activating model version {latest_version.version_tag} (ID: {latest_version.id})...")
        await model_repo.activate_version(latest_version.id)
        await session.commit()
        print(f"Activated model version {latest_version.version_tag} successfully!")
        print("You can now go back to the Valuation page and predict prices!")

if __name__ == "__main__":
    asyncio.run(activate())
