"""
Script to setup test databases for backend testing
"""
import asyncio
import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "")
USER_DB_NAME = os.getenv("USER_DB_NAME", "ecomoveX_users")
DEST_DB_NAME = os.getenv("DEST_DB_NAME", "ecomoveX_destinations")

TEST_USER_DB = f"test_{USER_DB_NAME}"
TEST_DEST_DB = f"test_{DEST_DB_NAME}"


async def create_test_databases():
    """Create test databases if they don't exist"""
    try:
        # Connect to PostgreSQL server
        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database="postgres"
        )
        
        print(f"✓ Connected to PostgreSQL server at {DB_HOST}:{DB_PORT}")
        
        # Check and create test user database
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            TEST_USER_DB
        )
        
        if not exists:
            await conn.execute(f'CREATE DATABASE "{TEST_USER_DB}"')
            print(f"✓ Created test database: {TEST_USER_DB}")
        else:
            print(f"✓ Test database already exists: {TEST_USER_DB}")
        
        # Check and create test destination database
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            TEST_DEST_DB
        )
        
        if not exists:
            await conn.execute(f'CREATE DATABASE "{TEST_DEST_DB}"')
            print(f"✓ Created test database: {TEST_DEST_DB}")
        else:
            print(f"✓ Test database already exists: {TEST_DEST_DB}")
        
        await conn.close()
        print("\n✓ Test databases setup complete!")
        return True
        
    except Exception as e:
        print(f"\n✗ Error setting up test databases: {e}")
        print("\nPlease ensure:")
        print(f"  1. PostgreSQL is running on {DB_HOST}:{DB_PORT}")
        print(f"  2. User '{DB_USER}' has permission to create databases")
        print(f"  3. Database credentials in .env are correct")
        return False


if __name__ == "__main__":
    print("Setting up test databases...\n")
    success = asyncio.run(create_test_databases())
    exit(0 if success else 1)
