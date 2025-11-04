# Test User Repository
import pytest
from repository.user_repository import UserRepository
from schema.authentication_schema import UserRegister
from schema.user_schema import UserCredentialUpdate, UserProfileUpdate
from models.user import Rank

@pytest.mark.asyncio
async def test_create_user(user_db_session):
    """Test creating a new user"""
    user_data = UserRegister(
        username="testuser",
        email="test@example.com",
        password="hashedpassword123"
    )
    
    user = await UserRepository.create_user(user_db_session, user_data)
    
    assert user is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.eco_point == 0
    assert user.rank == Rank.bronze.value

@pytest.mark.asyncio
async def test_get_user_by_email(user_db_session):
    """Test getting user by email"""
    # Create user first
    user_data = UserRegister(
        username="testuser2",
        email="test2@example.com",
        password="hashedpassword123"
    )
    created_user = await UserRepository.create_user(user_db_session, user_data)
    
    # Retrieve user by email
    user = await UserRepository.get_user_by_email(user_db_session, "test2@example.com")
    
    assert user is not None
    assert user.email == "test2@example.com"
    assert user.id == created_user.id

@pytest.mark.asyncio
async def test_get_user_by_id(user_db_session):
    """Test getting user by ID"""
    # Create user first
    user_data = UserRegister(
        username="testuser3",
        email="test3@example.com",
        password="hashedpassword123"
    )
    created_user = await UserRepository.create_user(user_db_session, user_data)
    
    # Retrieve user by ID
    user = await UserRepository.get_user_by_id(user_db_session, created_user.id)
    
    assert user is not None
    assert user.id == created_user.id
    assert user.username == "testuser3"

@pytest.mark.asyncio
async def test_update_user_credentials(user_db_session):
    """Test updating user credentials"""
    # Create user first
    user_data = UserRegister(
        username="testuser4",
        email="test4@example.com",
        password="hashedpassword123"
    )
    created_user = await UserRepository.create_user(user_db_session, user_data)
    
    # Update credentials
    update_data = UserCredentialUpdate(
        old_password="hashedpassword123",
        new_username="updateduser",
        new_email="updated@example.com"
    )
    updated_user = await UserRepository.update_user_credentials(
        user_db_session, created_user.id, update_data
    )
    
    assert updated_user is not None
    assert updated_user.username == "updateduser"
    assert updated_user.email == "updated@example.com"

@pytest.mark.asyncio
async def test_update_user_profile(user_db_session):
    """Test updating user profile"""
    # Create user first
    user_data = UserRegister(
        username="testuser5",
        email="test5@example.com",
        password="hashedpassword123"
    )
    created_user = await UserRepository.create_user(user_db_session, user_data)
    
    # Update profile
    update_data = UserProfileUpdate(
        eco_point=100,
        rank=Rank.silver
    )
    updated_user = await UserRepository.update_user_profile(
        user_db_session, created_user.id, update_data
    )
    
    assert updated_user is not None
    assert updated_user.eco_point == 100
    assert updated_user.rank == Rank.silver.value

@pytest.mark.asyncio
async def test_delete_user(user_db_session):
    """Test deleting a user"""
    # Create user first
    user_data = UserRegister(
        username="testuser6",
        email="test6@example.com",
        password="hashedpassword123"
    )
    created_user = await UserRepository.create_user(user_db_session, user_data)
    
    # Delete user
    success = await UserRepository.delete_user(user_db_session, created_user.id)
    
    assert success is True
    
    # Verify user is deleted
    deleted_user = await UserRepository.get_user_by_id(user_db_session, created_user.id)
    assert deleted_user is None
