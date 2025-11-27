import sys
from pathlib import Path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
import asyncio
import asyncpg
from utils.config import settings
from init_database import init_db

async def create_databases():
    conn = await asyncpg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASS,
        database='postgres'
    )
    
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", 
            settings.DB_NAME
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{settings.DB_NAME}"')
            print(f"Created database: {settings.DB_NAME}")
        else:
            print(f"Database already exists: {settings.DB_NAME}")
                        
    finally:
        await conn.close()
    
    print("\nInitializing user database tables...")
    await init_db(drop_all=False)

    print("\nDatabase initialization completed successfully")

if __name__ == "__main__":
    asyncio.run(create_databases())
