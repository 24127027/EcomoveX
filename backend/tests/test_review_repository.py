# Test Review Repository
import pytest
from repository.review_repository import ReviewRepository
from repository.user_repository import UserRepository
from repository.destination_repository import DestinationRepository
from schema.review_schema import ReviewCreate, ReviewUpdate
from schema.authentication_schema import UserRegister
from schema.destination_schema import DestinationCreate
from models.review import ReviewStatus

@pytest.mark.asyncio
async def test_create_review(user_db_session, dest_db_session):
    """Test creating a review (cross-database operation)"""
    # Create user
    user_data = UserRegister(
        username="reviewuser",
        email="review@example.com",
        password="hashedpassword123"
    )
    user = await UserRepository.create_user(user_db_session, user_data)
    
    # Create destination in destination DB
    dest_data = DestinationCreate(
        name="Test Place",
        longitude=105.8526,
        latitude=21.0285
    )
    destination = await DestinationRepository.create_destination(dest_db_session, dest_data)
    
    # Create review
    review_data = ReviewCreate(
        destination_id=destination.id,
        content="Great place to visit!",
        status=ReviewStatus.published
    )
    
    review = await ReviewRepository.create_review(user_db_session, review_data, user.id)
    
    assert review is not None
    assert review.user_id == user.id
    assert review.destination_id == destination.id
    assert review.content == "Great place to visit!"
    assert review.status == ReviewStatus.published

@pytest.mark.asyncio
async def test_get_reviews_by_destination(user_db_session, dest_db_session):
    """Test getting all reviews for a destination"""
    # Create users
    user1_data = UserRegister(username="reviewer1", email="r1@example.com", password="pass123")
    user1 = await UserRepository.create_user(user_db_session, user1_data)
    
    user2_data = UserRegister(username="reviewer2", email="r2@example.com", password="pass123")
    user2 = await UserRepository.create_user(user_db_session, user2_data)
    
    # Create destination
    dest_data = DestinationCreate(name="Popular Place", longitude=105.1, latitude=21.1)
    destination = await DestinationRepository.create_destination(dest_db_session, dest_data)
    
    # Create reviews
    review1_data = ReviewCreate(
        destination_id=destination.id,
        content="Review 1",
        status=ReviewStatus.published
    )
    await ReviewRepository.create_review(user_db_session, review1_data, user1.id)
    
    review2_data = ReviewCreate(
        destination_id=destination.id,
        content="Review 2",
        status=ReviewStatus.published
    )
    await ReviewRepository.create_review(user_db_session, review2_data, user2.id)
    
    # Get reviews
    reviews = await ReviewRepository.get_reviews_by_destination(user_db_session, destination.id)
    
    assert len(reviews) == 2
    assert all(r.destination_id == destination.id for r in reviews)

@pytest.mark.asyncio
async def test_get_reviews_by_user(user_db_session, dest_db_session):
    """Test getting all reviews by a user"""
    # Create user
    user_data = UserRegister(username="reviewer3", email="r3@example.com", password="pass123")
    user = await UserRepository.create_user(user_db_session, user_data)
    
    # Create destinations
    dest1_data = DestinationCreate(name="Place 1", longitude=105.1, latitude=21.1)
    dest1 = await DestinationRepository.create_destination(dest_db_session, dest1_data)
    
    dest2_data = DestinationCreate(name="Place 2", longitude=105.2, latitude=21.2)
    dest2 = await DestinationRepository.create_destination(dest_db_session, dest2_data)
    
    # Create reviews
    review1_data = ReviewCreate(
        destination_id=dest1.id,
        content="Review for place 1",
        status=ReviewStatus.published
    )
    await ReviewRepository.create_review(user_db_session, review1_data, user.id)
    
    review2_data = ReviewCreate(
        destination_id=dest2.id,
        content="Review for place 2",
        status=ReviewStatus.published
    )
    await ReviewRepository.create_review(user_db_session, review2_data, user.id)
    
    # Get user's reviews
    reviews = await ReviewRepository.get_reviews_by_user(user_db_session, user.id)
    
    assert len(reviews) == 2
    assert all(r.user_id == user.id for r in reviews)

@pytest.mark.asyncio
async def test_update_review(user_db_session, dest_db_session):
    """Test updating a review"""
    # Create user and destination
    user_data = UserRegister(username="reviewer4", email="r4@example.com", password="pass123")
    user = await UserRepository.create_user(user_db_session, user_data)
    
    dest_data = DestinationCreate(name="Place", longitude=105.1, latitude=21.1)
    destination = await DestinationRepository.create_destination(dest_db_session, dest_data)
    
    # Create review
    review_data = ReviewCreate(
        destination_id=destination.id,
        content="Original review",
        status=ReviewStatus.draft
    )
    review = await ReviewRepository.create_review(user_db_session, review_data, user.id)
    
    # Update review
    update_data = ReviewUpdate(
        content="Updated review content",
        status=ReviewStatus.published
    )
    updated_review = await ReviewRepository.update_review(user_db_session, review.id, update_data)
    
    assert updated_review is not None
    assert updated_review.content == "Updated review content"
    assert updated_review.status == ReviewStatus.published

@pytest.mark.asyncio
async def test_delete_review(user_db_session, dest_db_session):
    """Test deleting a review"""
    # Create user and destination
    user_data = UserRegister(username="reviewer5", email="r5@example.com", password="pass123")
    user = await UserRepository.create_user(user_db_session, user_data)
    
    dest_data = DestinationCreate(name="Place", longitude=105.1, latitude=21.1)
    destination = await DestinationRepository.create_destination(dest_db_session, dest_data)
    
    # Create review
    review_data = ReviewCreate(
        destination_id=destination.id,
        content="To be deleted",
        status=ReviewStatus.published
    )
    review = await ReviewRepository.create_review(user_db_session, review_data, user.id)
    
    # Delete review
    success = await ReviewRepository.delete_review(user_db_session, review.id)
    
    assert success is True
    
    # Verify deleted
    deleted_review = await ReviewRepository.get_review_by_id(user_db_session, review.id)
    assert deleted_review is None
