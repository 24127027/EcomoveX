"""
Pytest configuration and shared fixtures for all tests
"""
import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from main import app
from database.user_database import UserBase, get_user_db
from database.destination_database import DestinationBase, get_destination_db
from utils.config import settings
from services.authentication_service import AuthenticationService

# Test database URLs
TEST_USER_DB = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/test_ecomovex_users"
TEST_DEST_DB = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/test_ecomovex_destinations"

# Create test engines
test_user_engine = create_async_engine(TEST_USER_DB, poolclass=NullPool, echo=False)
test_dest_engine = create_async_engine(TEST_DEST_DB, poolclass=NullPool, echo=False)

TestUserSessionLocal = sessionmaker(
    bind=test_user_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

TestDestSessionLocal = sessionmaker(
    bind=test_dest_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def setup_databases():
    """Setup test databases"""
    async with test_user_engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.drop_all)
        await conn.run_sync(UserBase.metadata.create_all)
    
    async with test_dest_engine.begin() as conn:
        await conn.run_sync(DestinationBase.metadata.drop_all)
        await conn.run_sync(DestinationBase.metadata.create_all)
    
    yield
    
    async with test_user_engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.drop_all)
    
    async with test_dest_engine.begin() as conn:
        await conn.run_sync(DestinationBase.metadata.drop_all)

@pytest_asyncio.fixture(autouse=True)
async def clean_database():
    """Clean all tables before each test"""
    # Clean before test
    async with test_user_engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.drop_all)
        await conn.run_sync(UserBase.metadata.create_all)
    
    async with test_dest_engine.begin() as conn:
        await conn.run_sync(DestinationBase.metadata.drop_all)
        await conn.run_sync(DestinationBase.metadata.create_all)
    
    yield
    
    # Clean after test
    async with test_user_engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.drop_all)
        await conn.run_sync(UserBase.metadata.create_all)
    
    async with test_dest_engine.begin() as conn:
        await conn.run_sync(DestinationBase.metadata.drop_all)
        await conn.run_sync(DestinationBase.metadata.create_all)

@pytest_asyncio.fixture
async def user_db_session(clean_database):
    """Get test user database session"""
    async with TestUserSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def dest_db_session(clean_database):
    """Get test destination database session"""
    async with TestDestSessionLocal() as session:
        yield session

async def override_get_user_db():
    """Override for user database dependency"""
    async with TestUserSessionLocal() as session:
        yield session

async def override_get_destination_db():
    """Override for destination database dependency"""
    async with TestDestSessionLocal() as session:
        yield session

# Override dependencies
app.dependency_overrides[get_user_db] = override_get_user_db
app.dependency_overrides[get_destination_db] = override_get_destination_db

@pytest_asyncio.fixture
async def client(setup_databases):
    """Get test client"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

@pytest_asyncio.fixture
async def test_user(user_db_session):
    """Create a test user"""
    from models.user import User
    
    user = User(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        eco_point=0,
        rank="Bronze"
    )
    user_db_session.add(user)
    await user_db_session.commit()
    await user_db_session.refresh(user)
    return user

@pytest.fixture
def auth_token(test_user):
    """Generate auth token for test user"""
    return AuthenticationService.create_access_token(test_user)

@pytest.fixture
def auth_headers(auth_token):
    """Generate auth headers"""
    return {"Authorization": f"Bearer {auth_token}"}

@pytest_asyncio.fixture
async def test_destination(dest_db_session):
    """Create a test destination"""
    from models.destination import Destination
    
    destination = Destination(
        longitude=106.6297,
        latitude=10.8231
    )
    dest_db_session.add(destination)
    await dest_db_session.commit()
    await dest_db_session.refresh(destination)
    return destination
