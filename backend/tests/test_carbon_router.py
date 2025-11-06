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
from models.carbon import CarbonEmission, VehicleType, FuelType
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
async def test_calculate_carbon_emission_success(test_user):
    token = create_token(test_user["id"], test_user["role"])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/carbon/calculate",
            json={
                "vehicle_type": "car",
                "distance_km": 100.0,
                "fuel_type": "petrol"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["vehicle_type"] == "car"
        assert data["distance_km"] == 100.0
        assert data["fuel_type"] == "petrol"
        assert "carbon_emission_kg" in data
        assert data["carbon_emission_kg"] >= 0

@pytest.mark.asyncio
async def test_calculate_carbon_emission_unauthorized(setup_database):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/carbon/calculate",
            json={
                "vehicle_type": "car",
                "distance_km": 100.0,
                "fuel_type": "petrol"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_calculate_carbon_emission_invalid_distance(test_user):
    token = create_token(test_user["id"], test_user["role"])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/carbon/calculate",
            json={
                "vehicle_type": "car",
                "distance_km": -10.0,
                "fuel_type": "petrol"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

@pytest.mark.asyncio
async def test_get_my_carbon_emissions_empty(test_user):
    token = create_token(test_user["id"], test_user["role"])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/carbon/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

@pytest.mark.asyncio
async def test_get_my_carbon_emissions_with_data(test_user):
    token = create_token(test_user["id"], test_user["role"])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create an emission
        await client.post(
            "/carbon/calculate",
            json={
                "vehicle_type": "car",
                "distance_km": 50.0,
                "fuel_type": "petrol"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Get emissions
        response = await client.get(
            "/carbon/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["distance_km"] == 50.0

@pytest.mark.asyncio
async def test_get_my_total_carbon(test_user):
    token = create_token(test_user["id"], test_user["role"])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create emissions
        await client.post(
            "/carbon/calculate",
            json={"vehicle_type": "car", "distance_km": 50.0, "fuel_type": "petrol"},
            headers={"Authorization": f"Bearer {token}"}
        )
        await client.post(
            "/carbon/calculate",
            json={"vehicle_type": "bus", "distance_km": 30.0, "fuel_type": "diesel"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Get total
        response = await client.get(
            "/carbon/me/total",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_carbon_emission_kg" in data
        assert data["total_carbon_emission_kg"] >= 0

@pytest.mark.asyncio
async def test_get_carbon_emission_by_id_success(test_user):
    token = create_token(test_user["id"], test_user["role"])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create emission
        create_response = await client.post(
            "/carbon/calculate",
            json={"vehicle_type": "car", "distance_km": 50.0, "fuel_type": "petrol"},
            headers={"Authorization": f"Bearer {token}"}
        )
        create_data = create_response.json(); emission_id = create_data.get("emission_id") or create_data.get("id")
        
        # Get by ID
        response = await client.get(
            f"/carbon/{emission_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert (data.get("emission_id") or data.get("id")) == emission_id

@pytest.mark.asyncio
async def test_update_carbon_emission_success(test_user):
    token = create_token(test_user["id"], test_user["role"])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create emission
        create_response = await client.post(
            "/carbon/calculate",
            json={"vehicle_type": "car", "distance_km": 50.0, "fuel_type": "petrol"},
            headers={"Authorization": f"Bearer {token}"}
        )
        create_data = create_response.json(); emission_id = create_data.get("emission_id") or create_data.get("id")
        
        # Update
        response = await client.put(
            f"/carbon/{emission_id}",
            json={"distance_km": 75.0},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["distance_km"] == 75.0

@pytest.mark.asyncio
async def test_delete_carbon_emission_success(test_user):
    token = create_token(test_user["id"], test_user["role"])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create emission
        create_response = await client.post(
            "/carbon/calculate",
            json={"vehicle_type": "car", "distance_km": 50.0, "fuel_type": "petrol"},
            headers={"Authorization": f"Bearer {token}"}
        )
        create_data = create_response.json(); emission_id = create_data.get("emission_id") or create_data.get("id")
        
        # Delete
        response = await client.delete(
            f"/carbon/{emission_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "deleted successfully" in str(response_data).lower() or ("message" in response_data and "deleted" in response_data["message"].lower())

@pytest.mark.asyncio
async def test_get_my_total_carbon_by_year(test_user):
    token = create_token(test_user["id"], test_user["role"])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create emission
        await client.post(
            "/carbon/calculate",
            json={"vehicle_type": "car", "distance_km": 50.0, "fuel_type": "petrol"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Get by year
        current_year = datetime.now().year
        response = await client.get(
            f"/carbon/me/total/year?year={current_year}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_carbon_emission_kg" in data or "summary" in data
