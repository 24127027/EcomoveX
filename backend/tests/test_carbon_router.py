"""
Tests for Carbon Router
"""
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_calculate_carbon_emission(client: AsyncClient, test_user, auth_headers):
    """Test calculating carbon emission"""
    response = await client.post("/carbon/calculate", headers=auth_headers, json={
        "vehicle_type": "car",
        "fuel_type": "petrol",
        "distance_km": 10.5
    })
    assert response.status_code == 201
    data = response.json()
    assert "emission_id" in data or "id" in data
    assert data["distance_km"] == 10.5

@pytest.mark.asyncio
async def test_get_my_carbon_emissions(client: AsyncClient, test_user, auth_headers):
    """Test getting my carbon emissions"""
    response = await client.get("/carbon/me", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_my_total_carbon(client: AsyncClient, test_user, auth_headers):
    """Test getting total carbon"""
    response = await client.get("/carbon/me/total", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_carbon_emission_kg" in data

@pytest.mark.asyncio
async def test_get_carbon_by_day(client: AsyncClient, test_user, auth_headers):
    """Test getting carbon by day"""
    from datetime import datetime
    date = datetime.now().strftime("%Y-%m-%d")
    response = await client.get(f"/carbon/me/total/day?date={date}", headers=auth_headers)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_update_carbon_emission(client: AsyncClient, test_user, auth_headers):
    """Test updating carbon emission"""
    # First create emission
    create_response = await client.post("/carbon/calculate", headers=auth_headers, json={
        "vehicle_type": "car",
        "fuel_type": "petrol",
        "distance_km": 10.0
    })
    emission_id = create_response.json().get("emission_id") or create_response.json().get("id")
    
    # Update emission
    response = await client.put(f"/carbon/{emission_id}", headers=auth_headers, json={
        "distance_km": 15.0
    })
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_delete_carbon_emission(client: AsyncClient, test_user, auth_headers):
    """Test deleting carbon emission"""
    # First create emission
    create_response = await client.post("/carbon/calculate", headers=auth_headers, json={
        "vehicle_type": "car",
        "fuel_type": "petrol",
        "distance_km": 10.0
    })
    emission_id = create_response.json().get("emission_id") or create_response.json().get("id")
    
    # Delete emission
    response = await client.delete(f"/carbon/{emission_id}", headers=auth_headers)
    assert response.status_code == 200
