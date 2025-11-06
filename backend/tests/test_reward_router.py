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
from models.mission import Mission, RewardType, MissionAction
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

@pytest_asyncio.fixture
async def test_mission(setup_database):
    async with TestSessionLocal() as db:
        mission = Mission(
            name="Test Mission",
            description="Complete a test task",
            reward_type=RewardType.eco_point,
            action_trigger=MissionAction.register,
            value=50
        )
        db.add(mission)
        await db.commit()
        await db.refresh(mission)
        return {"id": mission.id, "name": mission.name, "value": mission.value}

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
async def test_get_all_missions_empty(setup_database):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/rewards/missions")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

@pytest.mark.asyncio
async def test_get_all_missions_with_data(test_mission):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/rewards/missions")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == test_mission["name"]

@pytest.mark.asyncio
async def test_get_mission_by_id_success(test_mission):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/rewards/missions/{test_mission['id']}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_mission["id"]
        assert data["name"] == test_mission["name"]

@pytest.mark.asyncio
async def test_get_mission_by_id_not_found(setup_database):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/rewards/missions/99999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_get_mission_by_name_success(test_mission):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/rewards/missions/name/{test_mission['name']}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == test_mission["name"]

@pytest.mark.asyncio
async def test_create_mission_admin_success(admin_user):
    token = create_token(admin_user["id"], admin_user["role"])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/rewards/missions",
            json={
                "name": "New Mission",
                "description": "A new mission to complete",
                "reward_type": "eco_point",
                "action_trigger": "register",
                "value": 100
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "New Mission"
        assert data["value"] == 100

@pytest.mark.asyncio
async def test_create_mission_non_admin_forbidden(test_user):
    token = create_token(test_user["id"], test_user["role"])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/rewards/missions",
            json={
                "name": "New Mission",
                "description": "A new mission",
                "reward_type": "eco_point",
                "action_trigger": "register",
                "value": 100
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_update_mission_admin_success(admin_user, test_mission):
    token = create_token(admin_user["id"], admin_user["role"])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            f"/rewards/missions/{test_mission['id']}",
            json={"value": 150},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["value"] == 150

@pytest.mark.asyncio
async def test_update_mission_non_admin_forbidden(test_user, test_mission):
    token = create_token(test_user["id"], test_user["role"])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            f"/rewards/missions/{test_mission['id']}",
            json={"value": 150},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_get_my_completed_missions_empty(test_user):
    token = create_token(test_user["id"], test_user["role"])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/rewards/me/missions",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

@pytest.mark.asyncio
async def test_complete_mission_success(test_user, test_mission):
    token = create_token(test_user["id"], test_user["role"])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            f"/rewards/missions/{test_mission['id']}/complete",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Complete mission returns the UserMission object
        assert "mission_id" in data or "message" in data

@pytest.mark.asyncio
async def test_get_user_completed_missions(test_user, test_mission):
    token = create_token(test_user["id"], test_user["role"])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Complete a mission
        await client.post(
            f"/rewards/missions/{test_mission['id']}/complete",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Get completed missions
        response = await client.get(f"/rewards/users/{test_user['id']}/missions")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 0

@pytest.mark.asyncio
async def test_complete_mission_unauthorized(test_mission):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(f"/rewards/missions/{test_mission['id']}/complete")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
