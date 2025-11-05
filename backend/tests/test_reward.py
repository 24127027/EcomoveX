import pytest
from httpx import AsyncClient


class TestRewardEndpoints:
    """Test rewards and missions endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_all_missions(self, client: AsyncClient):
        """Test getting all missions"""
        response = await client.get("/rewards/missions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_create_mission_as_admin(self, client: AsyncClient, test_admin_token: str):
        """Test creating a mission as admin"""
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        mission_data = {
            "name": "Test Mission",
            "description": "Complete 10 eco-friendly trips",
            "reward_type": "eco_point",
            "action_trigger": "eco_trip",
            "value": 100
        }
        
        response = await client.post("/rewards/missions", json=mission_data, headers=headers)
        assert response.status_code == 201
        data = response.json()
        assert "mission_id" in data or "id" in data
        assert data["name"] == "Test Mission"
        assert data["value"] == 100
    
    @pytest.mark.asyncio
    async def test_create_mission_as_non_admin(self, client: AsyncClient, test_user_token: str):
        """Test creating mission as non-admin fails"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        mission_data = {
            "name": "Unauthorized Mission",
            "description": "Should fail",
            "reward_type": "eco_point",
            "action_trigger": "eco_trip",
            "value": 50
        }
        
        response = await client.post("/rewards/missions", json=mission_data, headers=headers)
        assert response.status_code in [403, 422]  # Either forbidden or validation error
    
    @pytest.mark.asyncio
    async def test_get_mission_by_id(self, client: AsyncClient, test_admin_token: str):
        """Test getting mission by ID"""
        # Create a mission first
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        mission_data = {
            "name": "Get Mission Test",
            "description": "Test getting mission",
            "reward_type": "eco_point",
            "action_trigger": "eco_trip",
            "value": 75
        }
        create_response = await client.post("/rewards/missions", json=mission_data, headers=headers)
        mission_id = create_response.json().get("mission_id") or create_response.json().get("id")
        
        response = await client.get(f"/rewards/missions/{mission_id}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("mission_id") == mission_id or data.get("id") == mission_id
        assert data["name"] == "Get Mission Test"
    
    @pytest.mark.asyncio
    async def test_get_mission_by_name(self, client: AsyncClient, test_admin_token: str):
        """Test getting mission by name"""
        # Create a mission first
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        mission_data = {
            "name": "Unique Mission Name",
            "description": "Test name search",
            "reward_type": "eco_point",
            "action_trigger": "eco_trip",
            "value": 80
        }
        await client.post("/rewards/missions", json=mission_data, headers=headers)
        
        response = await client.get("/rewards/missions/name/Unique Mission Name")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Unique Mission Name"
    
    @pytest.mark.asyncio
    async def test_update_mission_as_admin(self, client: AsyncClient, test_admin_token: str):
        """Test updating mission as admin"""
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        
        # Create a mission
        mission_data = {
            "name": "Update Test Mission",
            "description": "Original description",
            "reward_type": "eco_point",
            "action_trigger": "eco_trip",
            "value": 50
        }
        create_response = await client.post("/rewards/missions", json=mission_data, headers=headers)
        mission_id = create_response.json().get("mission_id") or create_response.json().get("id")
        
        # Update the mission
        update_data = {
            "description": "Updated description",
            "value": 100
        }
        response = await client.put(f"/rewards/missions/{mission_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["value"] == 100
    
    @pytest.mark.asyncio
    async def test_update_mission_as_non_admin(self, client: AsyncClient, test_user_token: str, test_admin_token: str):
        """Test updating mission as non-admin fails"""
        # Create mission as admin
        admin_headers = {"Authorization": f"Bearer {test_admin_token}"}
        mission_data = {
            "name": "Protected Mission",
            "description": "Cannot update",
            "reward_type": "eco_point",
            "action_trigger": "eco_trip",
            "value": 60
        }
        create_response = await client.post("/rewards/missions", json=mission_data, headers=admin_headers)
        mission_id = create_response.json().get("mission_id") or create_response.json().get("id")
        
        # Try to update as non-admin
        user_headers = {"Authorization": f"Bearer {test_user_token}"}
        update_data = {
            "description": "Unauthorized update"
        }
        response = await client.put(f"/rewards/missions/{mission_id}", json=update_data, headers=user_headers)
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_complete_mission(self, client: AsyncClient, test_user_token: str, test_admin_token: str):
        """Test completing a mission"""
        # Create a mission as admin
        admin_headers = {"Authorization": f"Bearer {test_admin_token}"}
        mission_data = {
            "name": "Complete Test Mission",
            "description": "Mission to complete",
            "reward_type": "eco_point",
            "action_trigger": "eco_trip",
            "value": 150
        }
        create_response = await client.post("/rewards/missions", json=mission_data, headers=admin_headers)
        mission_id = create_response.json().get("mission_id") or create_response.json().get("id")
        
        # Complete the mission as user
        user_headers = {"Authorization": f"Bearer {test_user_token}"}
        response = await client.post(f"/rewards/missions/{mission_id}/complete", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "completed" in str(data).lower()
    
    @pytest.mark.asyncio
    async def test_get_my_completed_missions(self, client: AsyncClient, test_user_token: str, test_admin_token: str):
        """Test getting user's completed missions"""
        # Create and complete a mission
        admin_headers = {"Authorization": f"Bearer {test_admin_token}"}
        mission_data = {
            "name": "My Completed Mission",
            "description": "Check completed missions",
            "reward_type": "eco_point",
            "action_trigger": "eco_trip",
            "value": 120
        }
        create_response = await client.post("/rewards/missions", json=mission_data, headers=admin_headers)
        mission_id = create_response.json().get("mission_id") or create_response.json().get("id")
        
        user_headers = {"Authorization": f"Bearer {test_user_token}"}
        await client.post(f"/rewards/missions/{mission_id}/complete", headers=user_headers)
        
        # Get completed missions
        response = await client.get("/rewards/me/missions", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_get_user_completed_missions(self, client: AsyncClient, test_user_token: str):
        """Test getting another user's completed missions"""
        # Get my user_id
        headers = {"Authorization": f"Bearer {test_user_token}"}
        profile = await client.get("/users/me", headers=headers)
        user_id = profile.json().get("user_id") or profile.json().get("id")
        
        response = await client.get(f"/rewards/users/{user_id}/missions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_mission(self, client: AsyncClient):
        """Test getting non-existent mission"""
        response = await client.get("/rewards/missions/999999")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_complete_nonexistent_mission(self, client: AsyncClient, test_user_token: str):
        """Test completing non-existent mission"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = await client.post("/rewards/missions/999999/complete", headers=headers)
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_create_mission_invalid_data(self, client: AsyncClient, test_admin_token: str):
        """Test creating mission with invalid data"""
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        mission_data = {
            "name": "",  # Empty name
            "description": "Invalid mission",
            "reward_type": "eco_point",
            "action_trigger": "eco_trip",
            "value": -10  # Negative value
        }
        
        response = await client.post("/rewards/missions", json=mission_data, headers=headers)
        assert response.status_code == 422  # Validation error
        response = await client.post("/rewards/missions", json=mission_data, headers=headers)
        assert response.status_code == 422  # Validation error
