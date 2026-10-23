import asyncio
import uuid
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import async_session, init_db
from app.services.notebook_service import create_notebook, delete_source, process_url_source

async def main():
    await init_db()
    async with async_session() as db:
        # Create a temp notebook
        nb = await create_notebook(db, "Source Delete Test")
        nb_id = nb.id
        print(f"Created notebook {nb_id}")
        
        # Add a URL source (this will process embedding and Neo4j storage)
        source = await process_url_source(db, nb_id, "https://example.com")
        source_id = source.id
        print(f"Created and processed source {source_id}, status: {source.status}")
        
        # Now try to delete the source
        try:
            success = await delete_source(db, source_id)
            print(f"Delete source success: {success}")
        except Exception as e:
            print(f"Error occurred during delete: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
