import pytest
from httpx import AsyncClient


class TestAuthentication:
    """Test authentication endpoints"""
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, client: AsyncClient):
        """Test successful user registration"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewPassword123!"
        }
        
        response = await client.post("/auth/register", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user_id" in data
        assert "role" in data
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, client: AsyncClient):
        """Test registration with duplicate email fails"""
        user_data = {
            "username": "user1",
            "email": "duplicate@example.com",
            "password": "Password123!"
        }
        
        # First registration
        response1 = await client.post("/auth/register", json=user_data)
        assert response1.status_code == 200
        
        # Second registration with same email
        user_data["username"] = "user2"
        response2 = await client.post("/auth/register", json=user_data)
        assert response2.status_code == 400
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_username(self, client: AsyncClient):
        """Test registration with duplicate username fails"""
        user_data = {
            "username": "duplicate_username",
            "email": "user1@example.com",
            "password": "Password123!"
        }
        
        # First registration
        response1 = await client.post("/auth/register", json=user_data)
        assert response1.status_code == 200
        
        # Second registration with same username
        user_data["email"] = "user2@example.com"
        response2 = await client.post("/auth/register", json=user_data)
        assert response2.status_code == 400
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """Test successful login"""
        # Register user first
        user_data = {
            "username": "loginuser",
            "email": "loginuser@example.com",
            "password": "LoginPassword123!"
        }
        await client.post("/auth/register", json=user_data)
        
        # Login
        login_data = {
            "email": "loginuser@example.com",
            "password": "LoginPassword123!"
        }
        response = await client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user_id" in data
        assert "role" in data
    
    @pytest.mark.asyncio
    async def test_login_invalid_email(self, client: AsyncClient):
        """Test login with invalid email fails"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "Password123!"
        }
        response = await client.post("/auth/login", json=login_data)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_login_invalid_password(self, client: AsyncClient):
        """Test login with invalid password fails"""
        # Register user first
        user_data = {
            "username": "passuser",
            "email": "passuser@example.com",
            "password": "CorrectPassword123!"
        }
        await client.post("/auth/register", json=user_data)
        
        # Login with wrong password
        login_data = {
            "email": "passuser@example.com",
            "password": "WrongPassword123!"
        }
        response = await client.post("/auth/login", json=login_data)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_register_invalid_email_format(self, client: AsyncClient):
        """Test registration with invalid email format"""
        user_data = {
            "username": "invaliduser",
            "email": "not-an-email",
            "password": "Password123!",
            "full_name": "Invalid User"
        }
        response = await client.post("/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error
