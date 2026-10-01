
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.report_service import ReportService
import uuid

async def main():
    engine = create_async_engine("sqlite+aiosqlite:///carpriceprediction.db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        from sqlalchemy import text
        result = await db.execute(text("SELECT id, user_id FROM predictions LIMIT 1"))
        row = result.fetchone()
        if not row:
            print("No predictions in DB")
            return
            
        pred_id, user_id = row
        print(f"Testing with prediction {pred_id} and user {user_id}")
        
        service = ReportService(db)
        try:
            pdf_bytes = await service.generate_prediction_report(uuid.UUID(pred_id), uuid.UUID(user_id))
            print(f"Success! PDF size: {len(pdf_bytes)} bytes")
            with open("test.pdf", "wb") as f:
                f.write(pdf_bytes)
        except Exception as e:
            import traceback
            traceback.print_exc()

asyncio.run(main())

