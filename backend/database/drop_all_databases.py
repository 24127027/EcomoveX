import asyncio
import asyncpg
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from utils.config import settings

async def drop_databases():
    """
    Drop both user and destination databases.
    WARNING: This will permanently delete all data!
    """
    conn = await asyncpg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASS,
        database='postgres'
    )
    
    try:
        # Terminate existing connections to the databases
        print("🔌 Terminating existing connections...")
        
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
        
        # Drop main user database
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", 
            settings.USER_DB_NAME
        )
        if exists:
            await conn.execute(f'DROP DATABASE "{settings.USER_DB_NAME}"')
            print(f"🗑️  Dropped main database: {settings.USER_DB_NAME}")
        else:
            print(f"ℹ️  Main database does not exist: {settings.USER_DB_NAME}")

        # Drop destination database
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", 
            settings.DEST_DB_NAME
        )
        if exists:
            await conn.execute(f'DROP DATABASE "{settings.DEST_DB_NAME}"')
            print(f"🗑️  Dropped destination database: {settings.DEST_DB_NAME}")
        else:
            print(f"ℹ️  Destination database does not exist: {settings.DEST_DB_NAME}")
            
        print("\n✅ All databases dropped successfully!")
        print("⚠️  All data has been permanently deleted!")
        
    except Exception as e:
        print(f"\n❌ Error dropping databases: {e}")
        raise
    finally:
        await conn.close()

async def drop_all():
    """
    Drop both production and test databases.
    WARNING: This will permanently delete ALL data!
    """
    print("=" * 60)
    print("⚠️  WARNING: DROPPING ALL DATABASES")
    print("=" * 60)
    print("\nThis will delete:")
    print(f"  - {settings.USER_DB_NAME} (main user database)")
    print(f"  - {settings.DEST_DB_NAME} (destination database)")
    print("  - test_ecomoveX_users (test database)")
    print("  - test_ecomoveX_destinations (test database)")
    print("\n" + "=" * 60)
    
    await drop_databases()
    print()    
    print("\n" + "=" * 60)
    print("✅ ALL DATABASES HAVE BEEN DROPPED!")
    print("=" * 60)

if __name__ == "__main__":
    import sys
    
    # Safety check - require confirmation
    print("=" * 60)
    print("⚠️  DATABASE DELETION WARNING")
    print("=" * 60)
    print("\nThis script will permanently delete ALL databases and data!")
    print("This action CANNOT be undone!")
    print("\nDatabases that will be dropped:")
    print(f"  1. {settings.USER_DB_NAME}")
    print(f"  2. {settings.DEST_DB_NAME}")
    print("  3. test_ecomoveX_users")
    print("  4. test_ecomoveX_destinations")
    print("\n" + "=" * 60)
    
    confirmation = input("\nType 'DELETE ALL' to confirm: ")
    
    if confirmation == "DELETE ALL":
        print("\n🔥 Proceeding with database deletion...\n")
        asyncio.run(drop_all())
    else:
        print("\n❌ Operation cancelled. No databases were deleted.")
        sys.exit(0)
