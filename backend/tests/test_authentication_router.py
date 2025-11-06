import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import status
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from main import app
from database.user_database import get_db, UserBase
from models.user import User, Role, Rank
from datetime import datetime, UTC

TEST_DB_URL = "postgresql+asyncpg://postgres:142857@localhost:5432/test_ecomovex_users"

test_engine = create_async_engine(
    TEST_DB_URL,
    echo=False,
    poolclass=NullPool
)
TestSessionLocal = sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)

async def get_test_db():
    async with TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = get_test_db

@pytest_asyncio.fixture(scope="function")
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.drop_all)
        await conn.run_sync(UserBase.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.drop_all)

@pytest.mark.asyncio
async def test_register_user_success(setup_database):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user_id" in data
        assert "role" in data

@pytest.mark.asyncio
async def test_register_user_duplicate_email(setup_database):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First registration
        await client.post("/auth/register", json={
            "username": "user1",
            "email": "duplicate@example.com",
            "password": "password123"
        })
        
        # Second registration with same email
        response = await client.post("/auth/register", json={
            "username": "user2",
            "email": "duplicate@example.com",
            "password": "password456"
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_register_user_invalid_email(setup_database):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/auth/register", json={
            "username": "testuser",
            "email": "invalid-email",
            "password": "password123"
        })
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

@pytest.mark.asyncio
async def test_login_user_success(setup_database):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register user first
        await client.post("/auth/register", json={
            "username": "testuser",
            "email": "login@example.com",
            "password": "password123"
        })
        
        # Login
        response = await client.post("/auth/login", json={
            "email": "login@example.com",
            "password": "password123"
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user_id" in data

@pytest.mark.asyncio
async def test_login_user_wrong_password(setup_database):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register user
        await client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        })
        
        # Login with wrong password
        response = await client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalid" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_login_user_nonexistent(setup_database):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "password123"
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_register_user_short_password(setup_database):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "123"
        })
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
