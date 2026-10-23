import asyncio
import uuid
import sys
import os

# Add parent directory to sys.path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import get_settings
from app.models.notebook import Notebook, Source
from app.services.notebook_service import create_notebook, delete_notebook, delete_source

settings = get_settings()
engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def test():
    async with async_session() as db:
        # Create a test notebook
        nb = await create_notebook(db, title="Test Notebook Delete")
        print(f"Created notebook {nb.id}")
        
        # Test delete
        success = await delete_notebook(db, nb.id)
        print(f"Delete notebook success: {success}")

if __name__ == "__main__":
    asyncio.run(test())
