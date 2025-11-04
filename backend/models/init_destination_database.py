import asyncio
import sys
from pathlib import Path

# Add backend directory to path if running from models folder
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from database.destination_database import DestinationBase, destination_engine
from models import *
from sqlalchemy import text

async def drop_specific_tables(table_names: list[str]):
    """Drop specific tables by name (deletes table structure + all data)"""
    async with destination_engine.begin() as conn:
        for table_name in table_names:
            print(f"⚠️  Dropping table: {table_name}")
            await conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
        print("✅ Tables dropped successfully!")

async def clear_table_data(table_names: list[str]):
    """Clear all data from tables but keep table structure"""
    async with destination_engine.begin() as conn:
        for table_name in table_names:
            print(f"🧹 Clearing data from table: {table_name}")
            await conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
        print("✅ Table data cleared successfully!")

async def init_destination_db(drop_all: bool = False):
    async with destination_engine.begin() as conn:
        if drop_all:
            print("⚠️  Dropping all existing destination tables with CASCADE...")
            await conn.execute(text("DROP SCHEMA public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
            await conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
            await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
        print("🧱  Creating destination tables...")
        await conn.run_sync(DestinationBase.metadata.create_all)
    print("✅ Destination database initialized successfully!")

# if __name__ == "__main__":
    # Option 1: Clear data from specific tables (keeps table structure)
    # asyncio.run(clear_table_data(["destinations"]))
    
    # Option 2: Drop specific tables completely (deletes structure + data)
    # asyncio.run(drop_specific_tables(["destinations"]))
    
    # Option 3: Drop all tables and recreate
    # asyncio.run(init_destination_db(drop_all=True))
    
    # Option 4: Only create missing tables (safe - keeps data)
    # asyncio.run(init_destination_db(drop_all=False))
