"""
Tests for Review Router
"""
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_review(client: AsyncClient, test_user, test_destination, auth_headers):
    """Test creating a review"""
    response = await client.post("/reviews/", headers=auth_headers, json={
        "destination_id": test_destination.id,
        "rating": 5,
        "content": "Great place!"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["rating"] == 5

@pytest.mark.asyncio
async def test_get_reviews_by_destination(client: AsyncClient, test_destination):
    """Test getting reviews by destination"""
    response = await client.get(f"/reviews/destination/{test_destination.id}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_my_reviews(client: AsyncClient, test_user, auth_headers):
    """Test getting my reviews"""
    response = await client.get("/reviews/me", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_update_review(client: AsyncClient, test_user, test_destination, auth_headers):
    """Test updating a review"""
    # Create review first
    create_response = await client.post("/reviews/", headers=auth_headers, json={
        "destination_id": test_destination.id,
        "rating": 4,
        "content": "Good"
    })
    review_id = create_response.json().get("review_id") or create_response.json().get("id")
    
    # Update review
    response = await client.put(f"/reviews/{review_id}", headers=auth_headers, json={
        "rating": 5,
        "content": "Excellent!"
    })
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_delete_review(client: AsyncClient, test_user, test_destination, auth_headers):
    """Test deleting a review"""
    # Create review first
    create_response = await client.post("/reviews/", headers=auth_headers, json={
        "destination_id": test_destination.id,
        "rating": 3
    })
    review_id = create_response.json().get("review_id") or create_response.json().get("id")
    
    # Delete review
    response = await client.delete(f"/reviews/{review_id}", headers=auth_headers)
    assert response.status_code == 200
