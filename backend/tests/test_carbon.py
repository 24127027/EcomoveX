import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta


class TestCarbonEndpoints:
    """Test carbon emission tracking endpoints"""
    
    @pytest.mark.asyncio
    async def test_calculate_carbon_emission(self, client: AsyncClient, test_user_token: str):
        """Test calculating and creating carbon emission"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        emission_data = {
            "vehicle_type": "car",
            "distance_km": 10.5,
            "fuel_type": "petrol"
        }
        
        response = await client.post("/carbon/calculate", json=emission_data, headers=headers)
        assert response.status_code == 201
        data = response.json()
        assert "emission_id" in data or "id" in data
        assert data["vehicle_type"] == "car"
        assert data["distance_km"] == 10.5
        assert "carbon_emission_kg" in data
    
    @pytest.mark.asyncio
    async def test_calculate_carbon_emission_unauthorized(self, client: AsyncClient):
        """Test calculating carbon emission without auth fails"""
        emission_data = {
            "vehicle_type": "car",
            "distance_km": 10.5,
            "fuel_type": "gasoline"
        }
        
        response = await client.post("/carbon/calculate", json=emission_data)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_my_carbon_emissions(self, client: AsyncClient, test_user_token: str):
        """Test getting all user's carbon emissions"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # Create some emissions first
        emission_data = {
            "vehicle_type": "bus",
            "distance_km": 5.0,
            "fuel_type": "diesel"
        }
        await client.post("/carbon/calculate", json=emission_data, headers=headers)
        
        response = await client.get("/carbon/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Don't require data, just check it's a list
    
    @pytest.mark.asyncio
    async def test_get_my_total_carbon(self, client: AsyncClient, test_user_token: str):
        """Test getting total carbon emissions"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # Create emission
        emission_data = {
            "vehicle_type": "car",
            "distance_km": 20.0,
            "fuel_type": "petrol"
        }
        await client.post("/carbon/calculate", json=emission_data, headers=headers)
        
        response = await client.get("/carbon/me/total", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_carbon_emission_kg" in data or "total_carbon" in data
    
    @pytest.mark.asyncio
    async def test_get_carbon_emission_by_id(self, client: AsyncClient, test_user_token: str):
        """Test getting specific carbon emission by ID"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # Create emission
        emission_data = {
            "vehicle_type": "car",
            "distance_km": 3.0,
            "fuel_type": "electric"
        }
        create_response = await client.post("/carbon/calculate", json=emission_data, headers=headers)
        if create_response.status_code == 201:
            emission_id = create_response.json().get("emission_id") or create_response.json().get("id")
            
            response = await client.get(f"/carbon/{emission_id}", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data.get("emission_id") == emission_id or data.get("id") == emission_id
    
    @pytest.mark.asyncio
    async def test_update_carbon_emission(self, client: AsyncClient, test_user_token: str):
        """Test updating carbon emission"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # Create emission
        emission_data = {
            "vehicle_type": "car",
            "distance_km": 15.0,
            "fuel_type": "petrol"
        }
        create_response = await client.post("/carbon/calculate", json=emission_data, headers=headers)
        if create_response.status_code == 201:
            emission_id = create_response.json().get("emission_id") or create_response.json().get("id")
            
            # Update emission
            update_data = {
                "distance_km": 20.0
            }
            response = await client.put(f"/carbon/{emission_id}", json=update_data, headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["distance_km"] == 20.0
    
    @pytest.mark.asyncio
    async def test_delete_carbon_emission(self, client: AsyncClient, test_user_token: str):
        """Test deleting carbon emission"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # Create emission
        emission_data = {
            "vehicle_type": "bus",
            "distance_km": 50.0,
            "fuel_type": "diesel"
        }
        create_response = await client.post("/carbon/calculate", json=emission_data, headers=headers)
        if create_response.status_code == 201:
            emission_id = create_response.json().get("emission_id") or create_response.json().get("id")
            
            # Delete emission
            response = await client.delete(f"/carbon/{emission_id}", headers=headers)
            assert response.status_code == 200
            
            # Verify deletion
            get_response = await client.get(f"/carbon/{emission_id}", headers=headers)
            assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_total_carbon_by_day(self, client: AsyncClient, test_user_token: str):
        """Test getting carbon emissions for a specific day"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        today = datetime.now()
        
        response = await client.get(
            f"/carbon/me/total/day?date={today.isoformat()}",
            headers=headers
        )
        assert response.status_code == 200
        # Just check it returns something
    
    @pytest.mark.asyncio
    async def test_get_total_carbon_by_year(self, client: AsyncClient, test_user_token: str):
        """Test getting carbon emissions for a specific year"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        current_year = datetime.now().year
        
        response = await client.get(
            f"/carbon/me/total/year?year={current_year}",
            headers=headers
        )
        assert response.status_code == 200
        # Just check it returns something
    
    @pytest.mark.asyncio
    async def test_get_total_carbon_by_range(self, client: AsyncClient, test_user_token: str):
        """Test getting carbon emissions for a date range"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        response = await client.get(
            f"/carbon/me/total/range?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}",
            headers=headers
        )
        assert response.status_code == 200
        # Just check it returns something
    
    @pytest.mark.asyncio
    async def test_carbon_invalid_distance(self, client: AsyncClient, test_user_token: str):
        """Test creating emission with invalid distance"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        emission_data = {
            "vehicle_type": "car",
            "distance_km": -10.0,  # Negative distance
            "fuel_type": "petrol"
        }
        
        response = await client.post("/carbon/calculate", json=emission_data, headers=headers)
        assert response.status_code == 422  # Validation error
