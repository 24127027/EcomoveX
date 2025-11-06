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
import os
from jose import jwt

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

@pytest_asyncio.fixture
async def test_user(setup_database):
    async with TestSessionLocal() as db:
        user = User(
            username="testuser",
            email="test@example.com",
            password="hashed_password",
            role=Role.user,
            eco_point=100,
            rank=Rank.bronze
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return {"id": user.id, "username": user.username, "email": user.email, "role": user.role.value}

@pytest_asyncio.fixture
async def admin_user(setup_database):
    async with TestSessionLocal() as db:
        user = User(
            username="admin",
            email="admin@example.com",
            password="hashed_password",
            role=Role.admin,
            eco_point=500,
            rank=Rank.gold
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return {"id": user.id, "username": user.username, "email": user.email, "role": user.role.value}

def create_token(user_id: int, role: str = "User"):
    from jose import jwt
    import time
    secret_key = os.getenv("SECRET_KEY", "your_secret_key_min_32_characters_long_change_this_in_production")
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": time.time() + 3600
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")

@pytest.mark.asyncio
async def test_get_my_profile_success(test_user):
    token = create_token(test_user["id"], test_user["role"])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_user["id"]
        assert data["username"] == test_user["username"]
        assert data["email"] == test_user["email"]

@pytest.mark.asyncio
async def test_get_my_profile_unauthorized(setup_database):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/users/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_get_user_by_id_success(test_user):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/users/{test_user['id']}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_user["id"]
        assert data["username"] == test_user["username"]

@pytest.mark.asyncio
async def test_get_user_by_id_not_found(setup_database):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/users/99999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_update_user_credentials_success(test_user):
    token = create_token(test_user["id"], test_user["role"])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            "/users/me/credentials",
            json={
                "old_password": "hashed_password",
                "new_username": "updateduser",
                "new_email": "updated@example.com"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "updateduser"
        assert data["email"] == "updated@example.com"

@pytest.mark.asyncio
async def test_update_user_profile_success(test_user):
    token = create_token(test_user["id"], test_user["role"])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            "/users/me/profile",
            json={
                "eco_point": 200,
                "rank": "Silver"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["eco_point"] == 200

@pytest.mark.asyncio
async def test_delete_user_success(test_user):
    token = create_token(test_user["id"], test_user["role"])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert "deleted successfully" in response.json()["message"].lower()

@pytest.mark.asyncio
async def test_add_eco_point_admin_success(admin_user):
    token = create_token(admin_user["id"], admin_user["role"])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/users/me/eco_point/add?point=50",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["eco_point"] >= 550

@pytest.mark.asyncio
async def test_add_eco_point_non_admin_forbidden(test_user):
    token = create_token(test_user["id"], test_user["role"])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/users/me/eco_point/add?point=50",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
