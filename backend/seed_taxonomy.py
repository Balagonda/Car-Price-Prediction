import asyncio
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.brand import Brand
from app.models.car_model import CarModel
from app.models.city import City

async def seed():
    print("Seeding taxonomy data from Docs/cars_24_combined.csv...")
    df = pd.read_csv("../Docs/cars_24_combined.csv", low_memory=False)
    
    # Standardize names
    df['brand'] = df['Car Name'].astype(str).str.split(' ').str[0].str.strip().str.title()
    df['model'] = df['Car Name'].astype(str).str.split(' ').str[1:].str.join(' ').str.strip().str.title()
    df['city'] = df['Location'].astype(str).str.strip().str.title()
    
    brands = df['brand'].unique().tolist()
    models = df[['brand', 'model']].drop_duplicates()
    cities = df['city'].unique().tolist()
    
    async with AsyncSessionLocal() as session:
        # Insert Brands
        for b in brands:
            if not b or b == 'Nan' or b == 'Unknown': continue
            existing = await session.scalar(select(Brand).where(Brand.name == b))
            if not existing:
                session.add(Brand(name=b))
        await session.commit()
        
        # Insert Cities
        for c in cities:
            if not c or c == 'Nan' or c == 'Unknown': continue
            existing = await session.scalar(select(City).where(City.name == c))
            if not existing:
                session.add(City(name=c, state="Unknown"))
        await session.commit()
        
        # Insert Models
        for _, row in models.iterrows():
            b = row['brand']
            m = row['model']
            if not b or b == 'Nan' or b == 'Unknown' or not m or m == 'Nan' or m == 'Unknown': continue
            
            brand_obj = await session.scalar(select(Brand).where(Brand.name == b))
            if brand_obj:
                existing_m = await session.scalar(select(CarModel).where(CarModel.name == m, CarModel.brand_id == brand_obj.id))
                if not existing_m:
                    session.add(CarModel(name=m, brand_id=brand_obj.id))
        await session.commit()
        
        print("Taxonomy seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed())
