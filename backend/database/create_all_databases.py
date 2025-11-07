import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import asyncio
import asyncpg
from utils.config import settings

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
            print(f"✅ Created main database: {settings.USER_DB_NAME}")
        else:
            print(f"ℹ️  Main database already exists: {settings.USER_DB_NAME}")

        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", 
            settings.DEST_DB_NAME
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{settings.DEST_DB_NAME}"')
            print(f"✅ Created destination database: {settings.DEST_DB_NAME}")
        else:
            print(f"ℹ️  Destination database already exists: {settings.DEST_DB_NAME}")
            
    finally:
        await conn.close()
    
    from models.init_user_database import init_db
    from models.init_destination_database import init_destination_db
    
    print("\n🧱 Initializing main database tables...")
    await init_db(drop_all=False)
    
    print("\n🧱 Initializing destination database tables...")
    await init_destination_db(drop_all=False)
    
    print("\n✅ All databases initialized successfully!")

if __name__ == "__main__":
    asyncio.run(create_databases())
