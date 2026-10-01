
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.core.config import settings

async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as db:
        res = await db.execute(text("""
            SELECT p.id, p.is_listed, v.manufacturing_year, b.name, m.name, v.kilometers_driven
            FROM predictions p
            JOIN vehicles v ON p.vehicle_id = v.id
            JOIN brands b ON v.brand_id = b.id
            JOIN car_models m ON v.car_model_id = m.id
            WHERE p.is_listed = true
        """))
        for row in res.fetchall():
            print(row)

asyncio.run(main())

