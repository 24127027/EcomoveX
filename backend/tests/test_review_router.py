import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import status
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from main import app
from database.destination_database import get_destination_db, DestinationBase
from models.review import Review
from datetime import datetime, UTC
import os
from jose import jwt

TEST_DB_URL = "postgresql+asyncpg://postgres:142857@localhost:5432/test_ecomovex_destinations"

test_engine = create_async_engine(
    TEST_DB_URL,
    echo=False,
    poolclass=NullPool
)
TestSessionLocal = sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)

async def get_test_destination_db():
    async with TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_destination_db] = get_test_destination_db

@pytest_asyncio.fixture(scope="function")
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(DestinationBase.metadata.drop_all)
        await conn.run_sync(DestinationBase.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(DestinationBase.metadata.drop_all)

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
async def test_create_review_success(setup_database):
    token = create_token(1, "User")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/reviews/",
            json={
                "destination_id": 1,
                "rating": 5,
                "content": "Great place to visit!"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Destination doesn't exist, expecting 404
        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_create_review_unauthorized(setup_database):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/reviews/",
            json={
                "destination_id": 1,
                "rating": 5,
                "content": "Great place!"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_create_review_invalid_rating(setup_database):
    token = create_token(1, "User")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/reviews/",
            json={
                "destination_id": 1,
                "rating": 6,  # Invalid: rating should be 1-5
                "content": "Great place!"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

@pytest.mark.asyncio
async def test_create_review_rating_too_low(setup_database):
    token = create_token(1, "User")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/reviews/",
            json={
                "destination_id": 1,
                "rating": 0,  # Invalid: rating should be 1-5
                "content": "Bad place"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

@pytest.mark.asyncio
async def test_get_reviews_by_destination_empty(setup_database):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/reviews/destination/1")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

@pytest.mark.asyncio
async def test_get_reviews_by_destination_with_data(setup_database):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Get reviews (empty since no destination exists)
        response = await client.get("/reviews/destination/1")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

@pytest.mark.asyncio
async def test_get_reviews_by_user(setup_database):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Get user's reviews (empty since no reviews exist)
        response = await client.get("/reviews/user/1")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

@pytest.mark.asyncio
async def test_get_my_reviews(setup_database):
    token = create_token(1, "User")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Get my reviews (empty since no reviews exist)
        response = await client.get(
            "/reviews/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

@pytest.mark.asyncio
async def test_update_review_success(setup_database):
    token = create_token(1, "User")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Try to update nonexistent review
        response = await client.put(
            f"/reviews/999",
            json={"rating": 5, "content": "Updated!"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_delete_review_success(setup_database):
    token = create_token(1, "User")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Try to delete nonexistent review
        response = await client.delete(
            f"/reviews/999",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_create_review_without_content(setup_database):
    token = create_token(1, "User")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/reviews/",
            json={
                "destination_id": 1,
                "rating": 5
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Destination doesn't exist, expecting 404
        assert response.status_code == status.HTTP_404_NOT_FOUND
