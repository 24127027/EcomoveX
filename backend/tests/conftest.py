import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator

from main import app
from database.user_database import get_db, UserBase
from database.destination_database import get_destination_db, DestinationBase
from models.init_user_database import init_db
from models.init_destination_database import init_destination_db
from utils.config import settings

# Test database URLs
TEST_USER_DB_URL = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/test_{settings.USER_DB_NAME}"
TEST_DEST_DB_URL = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/test_{settings.DEST_DB_NAME}"


# Test engines
test_user_engine = create_async_engine(TEST_USER_DB_URL, poolclass=NullPool, echo=False)
test_destination_engine = create_async_engine(TEST_DEST_DB_URL, poolclass=NullPool, echo=False)

# Session makers
TestUserSessionLocal = async_sessionmaker(
    bind=test_user_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

TestDestinationSessionLocal = async_sessionmaker(
    bind=test_destination_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def setup_test_databases():
    """Setup test databases before tests and teardown after."""
    # Create all tables
    async with test_user_engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.drop_all)
        await conn.run_sync(UserBase.metadata.create_all)
    
    async with test_destination_engine.begin() as conn:
        await conn.run_sync(DestinationBase.metadata.drop_all)
        await conn.run_sync(DestinationBase.metadata.create_all)
    
    yield
    
    # Cleanup after tests
    async with test_user_engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.drop_all)
    
    async with test_destination_engine.begin() as conn:
        await conn.run_sync(DestinationBase.metadata.drop_all)


@pytest.fixture
async def db_session(setup_test_databases) -> AsyncGenerator[AsyncSession, None]:
    """Get test database session."""
    async with TestUserSessionLocal() as session:
        yield session


@pytest.fixture
async def dest_db_session(setup_test_databases) -> AsyncGenerator[AsyncSession, None]:
    """Get test destination database session."""
    async with TestDestinationSessionLocal() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession, dest_db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database overrides."""
    
    async def override_get_db():
        yield db_session
    
    async def override_get_destination_db():
        yield dest_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_destination_db] = override_get_destination_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user_token(client: AsyncClient) -> str:
    """Create a test user and return authentication token."""
    user_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "TestPassword123!"
    }
    
    response = await client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    data = response.json()
    return data["access_token"]


@pytest.fixture
async def test_admin_token(client: AsyncClient, db_session: AsyncSession) -> str:
    """Create a test admin user and return authentication token."""
    from models.user import User, Role
    
    # Create admin user directly with plain password (will be used by auth service)
    admin_user = User(
        username="adminuser",
        email="admin@example.com",
        password="Admin1",  # Store plain password - auth service will validate
        role=Role.admin
    )
    
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)
    
    # Login to get token
    response = await client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "Admin1"}
    )
    assert response.status_code == 200
    data = response.json()
    return data["access_token"]


@pytest.fixture
def auth_headers(test_user_token: str) -> dict:
    """Get authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def admin_auth_headers(test_admin_token: str) -> dict:
    """Get authorization headers for admin requests."""
    return {"Authorization": f"Bearer {test_admin_token}"}
