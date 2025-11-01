import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from utils.config import settings

async def create_database():
    import asyncpg
    
    try:
        conn = await asyncpg.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASS,
            database='postgres' # Connect to an existing database first
        )
        
        result = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            settings.DB_NAME
        )
        
        if result:
            print(f"✓ Database '{settings.DB_NAME}' already exists")
        else:
            await conn.execute(f'CREATE DATABASE "{settings.DB_NAME}"')
            print(f"✓ Database '{settings.DB_NAME}' created successfully!")
        
        await conn.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nPlease check:")
        print("1. PostgreSQL is running")
        print("2. Credentials in local.env are correct")
        print("3. User has permission to create databases")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(create_database())
