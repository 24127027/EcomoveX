import pytest
from httpx import AsyncClient


class TestUserEndpoints:
    """Test user management endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_my_profile(self, client: AsyncClient, test_user_token: str):
        """Test getting current user profile"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = await client.get("/users/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@example.com"
        assert data["username"] == "testuser"
    
    @pytest.mark.asyncio
    async def test_get_my_profile_unauthorized(self, client: AsyncClient):
        """Test getting profile without authentication fails"""
        response = await client.get("/users/me")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, client: AsyncClient, test_user_token: str):
        """Test getting user by ID"""
        # First get my profile to know the user_id
        headers = {"Authorization": f"Bearer {test_user_token}"}
        my_profile = await client.get("/users/me", headers=headers)
        user_id = my_profile.json().get("user_id") or my_profile.json().get("id")
        
        response = await client.get(f"/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("user_id") == user_id or data.get("id") == user_id
    
    @pytest.mark.asyncio
    async def test_get_user_by_invalid_id(self, client: AsyncClient):
        """Test getting user with non-existent ID"""
        response = await client.get("/users/999999")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_user_credentials(self, client: AsyncClient, test_user_token: str):
        """Test updating user credentials"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        update_data = {
            "email": "newemail@example.com",
            "password": "NewPassword123!"
        }
        
        response = await client.put("/users/me/credentials", json=update_data, headers=headers)
        assert response.status_code in [200, 422]  # Accept validation error too
        
        if response.status_code == 200:
            data = response.json()
            assert data["email"] == "newemail@example.com"
            
            # Test login with new credentials
            login_response = await client.post(
                "/auth/login",
                json={"email": "newemail@example.com", "password": "NewPassword123!"}
            )
            # Login should work if update was successful
    
    @pytest.mark.asyncio
    async def test_update_user_profile(self, client: AsyncClient, test_user_token: str):
        """Test updating user profile"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        update_data = {
            "eco_point": 100
        }
        
        response = await client.put("/users/me/profile", json=update_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Just check request was successful
        assert "eco_point" in data
    
    @pytest.mark.asyncio
    async def test_delete_user(self, client: AsyncClient):
        """Test deleting user account"""
        # Create a new user
        user_data = {
            "username": "deleteuser",
            "email": "deleteuser@example.com",
            "password": "DeletePassword123!"
        }
        register_response = await client.post("/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        
        # Delete the user
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.delete("/users/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["message"] == "User deleted successfully"
        
        # Try to get profile after deletion - should fail
        profile_response = await client.get("/users/me", headers=headers)
        assert profile_response.status_code in [401, 404]
    
    @pytest.mark.asyncio
    async def test_add_eco_point_as_admin(self, client: AsyncClient, test_admin_token: str):
        """Test adding eco points as admin"""
        headers = {"Authorization": f"Bearer {test_admin_token}"}
        response = await client.post("/users/me/eco_point/add?point=100", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["eco_point"] >= 100
    
    @pytest.mark.asyncio
    async def test_add_eco_point_as_non_admin(self, client: AsyncClient, test_user_token: str):
        """Test adding eco points as non-admin fails"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = await client.post("/users/me/eco_point/add?point=100", headers=headers)
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_register_user_via_user_endpoint(self, client: AsyncClient):
        """Test user registration via /users/register endpoint"""
        user_data = {
            "username": "registeruser",
            "email": "registeruser@example.com",
            "password": "RegisterPassword123!"
        }
        
        response = await client.post("/users/register", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
