import asyncio
import asyncpg
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.config import settings
from .init_database import init_db, init_destination_db

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
            settings.USER_DB_NAME
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{settings.USER_DB_NAME}"')
            print(f"Created database: {settings.USER_DB_NAME}")
        else:
            print(f"Database already exists: {settings.USER_DB_NAME}")

        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", 
            settings.DEST_DB_NAME
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{settings.DEST_DB_NAME}"')
            print(f"Created database: {settings.DEST_DB_NAME}")
        else:
            print(f"Database already exists: {settings.DEST_DB_NAME}")
            
    finally:
        await conn.close()
    
    
    print("\nInitializing user database tables...")
    await init_db(drop_all=False)

    print("\nInitializing destination database tables...")
    await init_destination_db(drop_all=False)
    
    print("\nDatabase initialization completed successfully")

if __name__ == "__main__":
    asyncio.run(create_databases())