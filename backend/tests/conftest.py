# Test configuration and fixtures
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncConnection
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from database.user_database import UserBase
from database.destination_database import DestinationBase

# Test database URLs
TEST_USER_DB_URL = "postgresql+asyncpg://postgres:142857@localhost:5432/test_ecomovex_users"
TEST_DEST_DB_URL = "postgresql+asyncpg://postgres:142857@localhost:5432/test_ecomovex_destinations"

# Create test engines with NullPool to avoid connection reuse issues
test_user_engine = create_async_engine(TEST_USER_DB_URL, echo=False, poolclass=NullPool)
test_dest_engine = create_async_engine(TEST_DEST_DB_URL, echo=False, poolclass=NullPool)

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_databases():
    """Setup test databases before all tests"""
    # Create all tables
    async with test_user_engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.create_all)
    
    async with test_dest_engine.begin() as conn:
        await conn.run_sync(DestinationBase.metadata.create_all)
    
    yield
    
    # Drop all tables after tests
    async with test_user_engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.drop_all)
    
    async with test_dest_engine.begin() as conn:
        await conn.run_sync(DestinationBase.metadata.drop_all)
    
    # Dispose engines
    await test_user_engine.dispose()
    await test_dest_engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def user_db_session():
    """Create a fresh database session for each test"""
    async with AsyncSession(test_user_engine, expire_on_commit=False) as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture(scope="function")
async def dest_db_session():
    """Create a fresh destination database session for each test"""
    async with AsyncSession(test_dest_engine, expire_on_commit=False) as session:
        yield session
        await session.rollback()
