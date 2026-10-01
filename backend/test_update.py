import asyncio
import uuid
from app.core.database import engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import select, update
from app.models.prediction import Prediction

async def main():
    s_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with s_maker() as session:
        r = await session.execute(select(Prediction).limit(1))
        p = r.scalars().first()
        if p:
            print('Prediction:', p.id, p.user_id)
            stmt = update(Prediction).where(Prediction.id == p.id).values(is_listed=True)
            await session.execute(stmt)
            await session.commit()
            print('Success')
        else:
            print('No prediction found')

if __name__ == "__main__":
    asyncio.run(main())
