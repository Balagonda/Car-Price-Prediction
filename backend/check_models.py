import asyncio
from app.core.database import engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from app.models.car_model import CarModel
from app.models.brand import Brand
from sqlalchemy import select, func

async def main():
    s_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with s_maker() as session:
        # get all brands and count models
        query = select(Brand.name, func.count(CarModel.id)).join(CarModel).group_by(Brand.id)
        result = await session.execute(query)
        for brand, count in result:
            print(f"{brand}: {count} models")
            
        print("---")
        q2 = select(CarModel.name).join(Brand).where(Brand.name == 'BMW')
        r2 = await session.execute(q2)
        print("BMW Models:", [m for m in r2.scalars().all()])

if __name__ == "__main__":
    asyncio.run(main())
