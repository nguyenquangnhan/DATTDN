import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.config import get_settings
from app.models.notebook import Source

settings = get_settings()
engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def check():
    async with async_session() as db:
        stmt = select(Source).order_by(Source.created_at.desc())
        result = await db.execute(stmt)
        sources = result.scalars().all()
        
        if not sources:
            print("No sources found in the database.")
            return
            
        print(f"Found {len(sources)} sources:")
        for s in sources:
            print(f"- ID: {s.id}")
            print(f"  Name: {s.original_name}")
            print(f"  Type: {s.file_type.value if hasattr(s.file_type, 'value') else s.file_type}")
            print(f"  Status: {s.status.value if hasattr(s.status, 'value') else s.status}")
            print(f"  Error: {s.error_message}")
            print(f"  Page Count: {s.page_count}")
            print("-" * 40)

if __name__ == "__main__":
    asyncio.run(check())
