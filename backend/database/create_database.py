import asyncio
from dotenv import load_dotenv
import os
from pathlib import Path
import sys

backend_dir = Path(__file__).resolve().parent.parent
env_path = backend_dir / "local.env"
load_dotenv(dotenv_path=env_path)

SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

async def create_database():
    import asyncpg
    
    try:
        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database='postgres'
        )
        
        result = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            DB_NAME
        )
        
        if result:
            print(f"✓ Database '{DB_NAME}' already exists")
        else:
            await conn.execute(f'CREATE DATABASE "{DB_NAME}"')
            print(f"✓ Database '{DB_NAME}' created successfully!")
        
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
