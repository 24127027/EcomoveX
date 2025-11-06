import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from database.user_database import UserBase
from database.destination_database import DestinationBase

TEST_USER_DB_URL = "postgresql+asyncpg://postgres:142857@localhost:5432/test_ecomovex_users"
TEST_DEST_DB_URL = "postgresql+asyncpg://postgres:142857@localhost:5432/test_ecomovex_destinations"

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_databases():
    user_engine = create_async_engine(TEST_USER_DB_URL, echo=False, poolclass=NullPool)
    dest_engine = create_async_engine(TEST_DEST_DB_URL, echo=False, poolclass=NullPool)
    
    async with user_engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.create_all)
    
    async with dest_engine.begin() as conn:
        await conn.run_sync(DestinationBase.metadata.create_all)
    
    yield
    
    async with user_engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.drop_all)
    
    async with dest_engine.begin() as conn:
        await conn.run_sync(DestinationBase.metadata.drop_all)
    
    await user_engine.dispose()
    await dest_engine.dispose()
