"""
Script to create test databases
"""
import asyncio
import asyncpg

async def create_test_databases():
    """Create test databases"""
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='142857',
        database='postgres'
    )
    
    try:
        await conn.execute('DROP DATABASE IF EXISTS test_ecomovex_users')
        await conn.execute('DROP DATABASE IF EXISTS test_ecomovex_destinations')
        
        await conn.execute('CREATE DATABASE test_ecomovex_users')
        await conn.execute('CREATE DATABASE test_ecomovex_destinations')
        
        print("✅ Test databases created successfully!")
    except Exception as e:
        print(f"❌ Error creating test databases: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_test_databases())
