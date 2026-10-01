import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def main():
    engine = create_async_engine("postgresql+asyncpg://neondb_owner:npg_DImvAs3Zl7Oy@ep-flat-frog-az0wdm40-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require")
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT count(*) FROM variants"))
        print("Total variants:", res.scalar())
        
        res = await conn.execute(text("SELECT * FROM variants WHERE id = 1062"))
        print("Variant 1062:", res.fetchone())

if __name__ == "__main__":
    asyncio.run(main())
