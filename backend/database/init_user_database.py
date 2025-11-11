from sqlalchemy import text
from database.user_database import UserBase, user_engine
from models import *

async def drop_specific_tables(table_names: list[str]):
    """Drop specific tables by name (deletes table structure + all data)"""
    async with user_engine.begin() as conn:
        for table_name in table_names:
            print(f"Dropping table: {table_name}")
            await conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
        print("Tables dropped successfully")

async def clear_table_data(table_names: list[str]):
    """Clear all data from tables but keep table structure"""
    async with user_engine.begin() as conn:
        for table_name in table_names:
            print(f"Clearing data from table: {table_name}")
            await conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
        print("Table data cleared successfully")

async def init_user_db(drop_all: bool = False):
    async with user_engine.begin() as conn:
        if drop_all:
            print("Dropping existing tables with CASCADE...")
            await conn.execute(text("DROP SCHEMA public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
            await conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
            await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
        print("Creating user tables...")
        await conn.run_sync(UserBase.metadata.create_all)
    print("User database initialized successfully")