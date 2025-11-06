"""
Tests for User Router
"""
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_my_profile(client: AsyncClient, test_user, auth_headers):
    """Test getting current user profile"""
    response = await client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email

@pytest.mark.asyncio
async def test_get_user_by_id(client: AsyncClient, test_user):
    """Test getting user by ID"""
    response = await client.get(f"/users/{test_user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id

@pytest.mark.asyncio
async def test_get_nonexistent_user(client: AsyncClient):
    """Test getting non-existent user"""
    response = await client.get("/users/99999")
    assert response.status_code == 500

@pytest.mark.asyncio
async def test_update_user_credentials(client: AsyncClient, test_user, auth_headers):
    """Test updating user credentials"""
    response = await client.put("/users/me/credentials", headers=auth_headers, json={
        "old_password": "testpass123",
        "new_username": "updateduser"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "updateduser"

@pytest.mark.asyncio
async def test_update_user_profile(client: AsyncClient, test_user, auth_headers):
    """Test updating user profile"""
    response = await client.put("/users/me/profile", headers=auth_headers, json={
        "eco_point": 100
    })
    assert response.status_code == 200
    data = response.json()
    assert data["eco_point"] == 100

@pytest.mark.asyncio
async def test_add_eco_point(client: AsyncClient, test_user, auth_headers):
    """Test adding eco points (requires admin)"""
    response = await client.post("/users/me/eco_point/add?point=50", headers=auth_headers)
    # Returns 403 because test_user is not admin
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """Test accessing protected route without auth"""
    response = await client.get("/users/me")
    assert response.status_code == 401
