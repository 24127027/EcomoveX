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
from models.friend import Friend
from datetime import datetime, UTC

TEST_DB_URL = "postgresql+asyncpg://postgres:142857@localhost:5432/test_ecomovex_users"

test_engine = create_async_engine(
    TEST_DB_URL,
    echo=False,
    poolclass=NullPool  # Disable connection pooling for tests
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
async def test_users(setup_database):
    async with TestSessionLocal() as db:
        user1 = User(
            username="user1",
            email="user1@test.com",
            password="password123",
            role=Role.user,
            eco_point=0,
            rank=Rank.bronze
        )
        user2 = User(
            username="user2",
            email="user2@test.com",
            password="password123",
            role=Role.user,
            eco_point=0,
            rank=Rank.bronze
        )
        user3 = User(
            username="user3",
            email="user3@test.com",
            password="password123",
            role=Role.user,
            eco_point=0,
            rank=Rank.bronze
        )
        db.add_all([user1, user2, user3])
        await db.commit()
        await db.refresh(user1)
        await db.refresh(user2)
        await db.refresh(user3)
        return {
            "user1": {"id": user1.id, "username": user1.username, "email": user1.email},
            "user2": {"id": user2.id, "username": user2.username, "email": user2.email},
            "user3": {"id": user3.id, "username": user3.username, "email": user3.email}
        }

def create_token(user_id: int, role: str = "User"):
    from jose import jwt
    import time
    import os
    # Use the actual SECRET_KEY from config/env
    secret_key = os.getenv("SECRET_KEY", "your_secret_key_min_32_characters_long_change_this_in_production")
    token_data = {
        "sub": str(user_id),
        "role": role,
        "exp": int(time.time()) + 3600  # 1 hour from now in Unix timestamp
    }
    return jwt.encode(token_data, secret_key, algorithm="HS256")

@pytest.mark.asyncio
async def test_send_friend_request_success(test_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = create_token(test_users["user1"]["id"])
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.post(
            "/friends/request",
            json={"friend_id": test_users["user2"]["id"]},
            headers=headers
        )
        
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["user_id"] == test_users["user1"]["id"]
        assert data["friend_id"] == test_users["user2"]["id"]
        assert data["status"] == "Pending"
        assert "created_at" in data

@pytest.mark.asyncio
async def test_send_friend_request_to_self(test_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = create_token(test_users["user1"]["id"])
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.post(
            "/friends/request",
            json={"friend_id": test_users["user1"]["id"]},
            headers=headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot send friend request to yourself" in response.json()["detail"]

@pytest.mark.asyncio
async def test_send_friend_request_to_nonexistent_user(test_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = create_token(test_users["user1"]["id"])
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.post(
            "/friends/request",
            json={"friend_id": 99999},
            headers=headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_send_duplicate_friend_request(test_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = create_token(test_users["user1"]["id"])
        headers = {"Authorization": f"Bearer {token}"}
        
        await client.post(
            "/friends/request",
            json={"friend_id": test_users["user2"]["id"]},
            headers=headers
        )
        
        response = await client.post(
            "/friends/request",
            json={"friend_id": test_users["user2"]["id"]},
            headers=headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"]

@pytest.mark.asyncio
async def test_accept_friend_request_success(test_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token1 = create_token(test_users["user1"]["id"])
        token2 = create_token(test_users["user2"]["id"])
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        await client.post(
            "/friends/request",
            json={"friend_id": test_users["user2"]["id"]},
            headers=headers1
        )
        
        response = await client.post(
            f"/friends/{test_users['user1']['id']}/accept",
            headers=headers2
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "Accepted"

@pytest.mark.asyncio
async def test_accept_nonexistent_friend_request(test_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = create_token(test_users["user1"]["id"])
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.post(
            f"/friends/{test_users['user2']['id']}/accept",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_reject_friend_request_success(test_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token1 = create_token(test_users["user1"]["id"])
        token2 = create_token(test_users["user2"]["id"])
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        await client.post(
            "/friends/request",
            json={"friend_id": test_users["user2"]["id"]},
            headers=headers1
        )
        
        response = await client.delete(
            f"/friends/{test_users['user1']['id']}/reject",
            headers=headers2
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert "rejected successfully" in response.json()["message"]

@pytest.mark.asyncio
async def test_block_user_success(test_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = create_token(test_users["user1"]["id"])
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.post(
            f"/friends/{test_users['user2']['id']}/block",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "Blocked"

@pytest.mark.asyncio
async def test_block_self(test_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = create_token(test_users["user1"]["id"])
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.post(
            f"/friends/{test_users['user1']['id']}/block",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot block yourself" in response.json()["detail"]

@pytest.mark.asyncio
async def test_unblock_user_success(test_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = create_token(test_users["user1"]["id"])
        headers = {"Authorization": f"Bearer {token}"}
        
        await client.post(
            f"/friends/{test_users['user2']['id']}/block",
            headers=headers
        )
        
        response = await client.delete(
            f"/friends/{test_users['user2']['id']}/unblock",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert "unblocked successfully" in response.json()["message"]

@pytest.mark.asyncio
async def test_unfriend_success(test_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token1 = create_token(test_users["user1"]["id"])
        token2 = create_token(test_users["user2"]["id"])
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        await client.post(
            "/friends/request",
            json={"friend_id": test_users["user2"]["id"]},
            headers=headers1
        )
        
        await client.post(
            f"/friends/{test_users['user1']['id']}/accept",
            headers=headers2
        )
        
        response = await client.delete(
            f"/friends/{test_users['user2']['id']}",
            headers=headers1
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert "Unfriended successfully" in response.json()["message"]

@pytest.mark.asyncio
async def test_get_friends_empty(test_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = create_token(test_users["user1"]["id"])
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.get("/friends/", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

@pytest.mark.asyncio
async def test_get_friends_with_data(test_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token1 = create_token(test_users["user1"]["id"])
        token2 = create_token(test_users["user2"]["id"])
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        await client.post(
            "/friends/request",
            json={"friend_id": test_users["user2"]["id"]},
            headers=headers1
        )
        
        await client.post(
            f"/friends/{test_users['user1']['id']}/accept",
            headers=headers2
        )
        
        response = await client.get("/friends/", headers=headers1)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["friend_username"] == test_users["user2"]["username"]
        assert data[0]["friend_email"] == test_users["user2"]["email"]
        assert data[0]["status"] == "Accepted"

@pytest.mark.asyncio
async def test_get_pending_requests(test_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token1 = create_token(test_users["user1"]["id"])
        token2 = create_token(test_users["user2"]["id"])
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        await client.post(
            "/friends/request",
            json={"friend_id": test_users["user2"]["id"]},
            headers=headers1
        )
        
        response = await client.get("/friends/pending", headers=headers2)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["friend_username"] == test_users["user1"]["username"]
        assert data[0]["status"] == "Pending"

@pytest.mark.asyncio
async def test_get_sent_requests(test_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = create_token(test_users["user1"]["id"])
        headers = {"Authorization": f"Bearer {token}"}
        
        await client.post(
            "/friends/request",
            json={"friend_id": test_users["user2"]["id"]},
            headers=headers
        )
        
        response = await client.get("/friends/sent", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["friend_username"] == test_users["user2"]["username"]
        assert data[0]["status"] == "Pending"

@pytest.mark.asyncio
async def test_get_blocked_users(test_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = create_token(test_users["user1"]["id"])
        headers = {"Authorization": f"Bearer {token}"}
        
        await client.post(
            f"/friends/{test_users['user2']['id']}/block",
            headers=headers
        )
        
        response = await client.get("/friends/blocked", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["friend_username"] == test_users["user2"]["username"]
        assert data[0]["status"] == "Blocked"

@pytest.mark.asyncio
async def test_unauthorized_access(test_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/friends/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
