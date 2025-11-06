import asyncio
import asyncpg

async def create_test_databases():
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="142857",
        database="postgres"
    )
    
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = 'test_ecomovex_users'"
        )
        if not exists:
            await conn.execute('CREATE DATABASE test_ecomovex_users')
            print("✅ Created test user database")
        else:
            print("ℹ️  Test user database already exists")
        
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = 'test_ecomovex_destinations'"
        )
        if not exists:
            await conn.execute('CREATE DATABASE test_ecomovex_destinations')
            print("✅ Created test destination database")
        else:
            print("ℹ️  Test destination database already exists")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_test_databases())
