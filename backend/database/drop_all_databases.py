import asyncio
import asyncpg
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils.config import settings

async def drop_databases():
    conn = await asyncpg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASS,
        database='postgres'
    )
    
    try:

        print("Terminating active connections...")
        
        await conn.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{settings.USER_DB_NAME}'
            AND pid <> pg_backend_pid();
        """)
        
        await conn.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{settings.DEST_DB_NAME}'
            AND pid <> pg_backend_pid();
        """)
        

        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", 
            settings.USER_DB_NAME
        )
        if exists:
            await conn.execute(f'DROP DATABASE "{settings.USER_DB_NAME}"')
            print(f"Dropped database: {settings.USER_DB_NAME}")
        else:
            print(f"Database not found: {settings.USER_DB_NAME}")


        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", 
            settings.DEST_DB_NAME
        )
        if exists:
            await conn.execute(f'DROP DATABASE "{settings.DEST_DB_NAME}"')
            print(f"Dropped database: {settings.DEST_DB_NAME}")
        else:
            print(f"Database not found: {settings.DEST_DB_NAME}")
            
        print("\nAll databases dropped successfully")
        print("WARNING: All data has been permanently deleted")
        
    except Exception as e:
        print(f"\nERROR: Failed to drop databases - {e}")
        raise
    finally:
        await conn.close()

async def drop_all():
    print("=" * 60)
    print("WARNING: DROPPING ALL DATABASES")
    print("=" * 60)
    print("\nDatabases to be deleted:")
    print(f"  - {settings.USER_DB_NAME} (user database)")
    print(f"  - {settings.DEST_DB_NAME} (destination database)")
    print(f"  - test_ecomoveX_users (test database)")
    print(f"  - test_ecomoveX_destinations (test database)")
    print("\n" + "=" * 60)
    
    await drop_databases()
    print()    
    print("\n" + "=" * 60)
    print("DATABASE DELETION COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE DELETION WARNING")
    print("=" * 60)
    print("\nThis action will permanently delete ALL databases and data.")
    print("This operation cannot be undone.")
    print("\nDatabases to be dropped:")
    print(f"  1. {settings.USER_DB_NAME}")
    print(f"  2. {settings.DEST_DB_NAME}")
    print(f"  3. test_ecomoveX_users")
    print(f"  4. test_ecomoveX_destinations")
    print("\n" + "=" * 60)
    
    confirmation = input("\nType 'DELETE ALL' to confirm: ")
    
    if confirmation == "DELETE ALL":
        print("\nProceeding with database deletion...\n")
        asyncio.run(drop_all())
    else:
        print("\nOperation cancelled. No databases were deleted.")
        sys.exit(0)
