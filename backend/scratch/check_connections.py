import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.config import get_settings
from app.services.neo4j_service import get_neo4j_driver, get_gemini_client

async def test_postgres(settings):
    print("Testing PostgreSQL connection...")
    try:
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version();"))
            row = result.fetchone()
            print(" -> [OK] PostgreSQL connection successful!")
            print(f"    Version: {row[0] if row else 'Unknown'}")
        await engine.dispose()
        return True
    except Exception as e:
        print(f" -> [ERROR] PostgreSQL connection failed: {e}")
        return False

def test_neo4j():
    print("Testing Neo4j connection...")
    try:
        driver = get_neo4j_driver()
        with driver.session() as session:
            result = session.run("RETURN 'Connection OK' as val")
            row = result.single()
            print(" -> [OK] Neo4j connection successful!")
            print(f"    Value: {row['val'] if row else 'Unknown'}")
        return True
    except Exception as e:
        print(f" -> [ERROR] Neo4j connection failed: {e}")
        return False

def test_gemini():
    print("Testing Google Gemini API connection...")
    try:
        client = get_gemini_client()
        # Simple test prompt
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents='Hello, say "Gemini is ready!" if you read this.'
        )
        print(" -> [OK] Gemini API connection successful!")
        print(f"    Response: {response.text.strip()}")
        return True
    except Exception as e:
        print(f" -> [ERROR] Gemini API connection failed: {e}")
        return False

async def main():
    settings = get_settings()
    print("=" * 60)
    print("        SYSTEM DIAGNOSTICS & CONNECTION CHECKS")
    print("=" * 60)
    
    pg_ok = await test_postgres(settings)
    print("-" * 60)
    
    neo_ok = test_neo4j()
    print("-" * 60)
    
    gemini_ok = test_gemini()
    print("=" * 60)
    
    if pg_ok and neo_ok and gemini_ok:
        print("SUCCESS: ALL SYSTEMS ARE FUNCTIONAL AND READY TO GO!")
    else:
        print("WARNING: SOME SYSTEMS FAILED. Please check the logs/errors above.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
