import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://neondb_owner:npg_DImvAs3Zl7Oy@ep-flat-frog-az0wdm40-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require")
    
    # Check if 1062 exists in variants
    val = await conn.fetchval("SELECT name FROM variants WHERE id = $1", 1062)
    print("Variant 1062 name:", val)
    
    # Check how many variants there are
    count = await conn.fetchval("SELECT count(*) FROM variants")
    print("Total variants:", count)
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
