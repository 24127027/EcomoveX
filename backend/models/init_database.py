import asyncio
from database.database import Base, engine
from models import *

async def init_db(drop_all: bool = False):
    async with engine.begin() as conn:
        if drop_all:
            print("⚠️  Dropping all existing tables...")
            await conn.run_sync(Base.metadata.drop_all)
        print("🧱  Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(init_db(drop_all=True))