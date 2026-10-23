import asyncio
import uuid
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import async_session, init_db
from app.services.notebook_service import create_notebook, delete_notebook

async def main():
    await init_db()
    async with async_session() as db:
        # Create a temp notebook
        nb = await create_notebook(db, "Notebook Delete Test")
        nb_id = nb.id
        print(f"Created notebook {nb_id}")
        
        # Now try to delete the notebook
        try:
            success = await delete_notebook(db, nb_id)
            print(f"Delete notebook success: {success}")
        except Exception as e:
            print(f"Error occurred during delete: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
