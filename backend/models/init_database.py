import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

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