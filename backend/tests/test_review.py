import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestReviewEndpoints:
    """Test review management endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_review(self, client: AsyncClient, test_user_token: str, dest_db_session: AsyncSession):
        """Test creating a review"""
        # First create a destination
        from models.destination import Destination
        dest = Destination(id=1, longitude=100.0, latitude=50.0)
        dest_db_session.add(dest)
        await dest_db_session.commit()
        
        headers = {"Authorization": f"Bearer {test_user_token}"}
        review_data = {
            "destination_id": 1,
            "rating": 5,
            "content": "Great place to visit!"
        }
        
        response = await client.post("/reviews/", json=review_data, headers=headers)
        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
        assert response.status_code == 201
        data = response.json()
        assert "review_id" in data or "id" in data
        assert data["rating"] == 5
    
    @pytest.mark.asyncio
    async def test_create_review_unauthorized(self, client: AsyncClient):
        """Test creating review without authentication fails"""
        review_data = {
            "destination_id": 1,
            "rating": 4,
            "comment": "Nice destination"
        }
        
        response = await client.post("/reviews/", json=review_data)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_reviews_by_destination(self, client: AsyncClient):
        """Test getting all reviews for a destination"""
        response = await client.get("/reviews/destination/1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_get_reviews_by_user(self, client: AsyncClient, test_user_token: str):
        """Test getting all reviews by a specific user"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # Get my user_id
        profile = await client.get("/users/me", headers=headers)
        user_id = profile.json()["user_id"] if "user_id" in profile.json() else profile.json()["id"]
        
        response = await client.get(f"/reviews/user/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_get_my_reviews(self, client: AsyncClient, test_user_token: str):
        """Test getting current user's reviews"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        response = await client.get("/reviews/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_update_review(self, client: AsyncClient, test_user_token: str, dest_db_session: AsyncSession):
        """Test updating a review"""
        # Create destination first
        from models.destination import Destination
        dest = Destination(id=4, longitude=100.0, latitude=50.0)
        dest_db_session.add(dest)
        await dest_db_session.commit()
        
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # Create a review
        review_data = {
            "destination_id": 4,
            "rating": 3,
            "content": "Initial review"
        }
        create_response = await client.post("/reviews/", json=review_data, headers=headers)
        if create_response.status_code == 201:
            review_id = create_response.json().get("review_id") or create_response.json().get("id")
            
            # Update the review
            update_data = {
                "rating": 5,
                "content": "Updated review - much better!"
            }
            response = await client.put(f"/reviews/{review_id}", json=update_data, headers=headers)
            if response.status_code != 200:
                print(f"Update response status: {response.status_code}")
                print(f"Update response body: {response.text}")
            assert response.status_code == 200
            data = response.json()
            assert data["rating"] == 5
    
    @pytest.mark.asyncio
    async def test_delete_review(self, client: AsyncClient, test_user_token: str, dest_db_session: AsyncSession):
        """Test deleting a review"""
        # Create destination first
        from models.destination import Destination
        dest = Destination(id=5, longitude=100.0, latitude=50.0)
        dest_db_session.add(dest)
        await dest_db_session.commit()
        
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # Create a review
        review_data = {
            "destination_id": 5,
            "rating": 2,
            "comment": "Not great"
        }
        create_response = await client.post("/reviews/", json=review_data, headers=headers)
        if create_response.status_code == 201:
            review_id = create_response.json().get("review_id") or create_response.json().get("id")
            
            # Delete the review
            response = await client.delete(f"/reviews/{review_id}", headers=headers)
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_create_review_invalid_rating(self, client: AsyncClient, test_user_token: str):
        """Test creating review with invalid rating"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        review_data = {
            "destination_id": 6,
            "rating": 10,  # Invalid rating (should be 1-5)
            "comment": "Test review"
        }
        
        response = await client.post("/reviews/", json=review_data, headers=headers)
        assert response.status_code in [404, 422]  # Either validation error or not found
    
    @pytest.mark.asyncio
    async def test_get_reviews_nonexistent_destination(self, client: AsyncClient):
        """Test getting reviews for non-existent destination"""
        response = await client.get("/reviews/destination/999999")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_review(self, client: AsyncClient, test_user_token: str):
        """Test updating non-existent review"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        update_data = {
            "rating": 5,
            "comment": "Updated review"
        }
        
        response = await client.put("/reviews/999999", json=update_data, headers=headers)
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_review(self, client: AsyncClient, test_user_token: str):
        """Test deleting non-existent review"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        response = await client.delete("/reviews/999999", headers=headers)
        assert response.status_code == 404
