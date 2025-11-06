"""
Tests for Reward Router
"""
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_all_missions(client: AsyncClient):
    """Test getting all missions"""
    response = await client.get("/rewards/missions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_create_mission(client: AsyncClient, auth_headers):
    """Test creating a mission (requires admin)"""
    response = await client.post("/rewards/missions", headers=auth_headers, json={
        "name": "Test Mission",
        "description": "Complete test",
        "reward_type": "eco_point",
        "action_trigger": "register",
        "value": 10
    })
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_get_mission_by_id(client: AsyncClient):
    """Test getting mission by ID"""
    # Create mission first
    response = await client.get("/rewards/missions")
    if len(response.json()) > 0:
        mission_id = response.json()[0]["id"]
        response = await client.get(f"/rewards/missions/{mission_id}")
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_my_completed_missions(client: AsyncClient, test_user, auth_headers):
    """Test getting my completed missions"""
    response = await client.get("/rewards/me/missions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    # Response should be a list or dict with missions key
    if isinstance(data, dict):
        assert "missions" in data
    else:
        assert isinstance(data, list)
