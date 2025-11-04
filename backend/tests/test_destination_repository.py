# Test Destination Repository
import pytest
from repository.destination_repository import DestinationRepository
from schema.destination_schema import DestinationCreate, DestinationUpdate

@pytest.mark.asyncio
async def test_create_destination(dest_db_session):
    """Test creating a new destination"""
    dest_data = DestinationCreate(
        longitude=105.8342,
        latitude=21.0278
    )
    
    destination = await DestinationRepository.create_destination(dest_db_session, dest_data)
    
    assert destination is not None
    assert destination.longitude == 105.8342
    assert destination.latitude == 21.0278

@pytest.mark.asyncio
async def test_get_destination_by_id(dest_db_session):
    """Test getting destination by ID"""
    # Create destination first
    dest_data = DestinationCreate(
        longitude=106.8342,
        latitude=22.0278
    )
    created_dest = await DestinationRepository.create_destination(dest_db_session, dest_data)
    
    # Retrieve destination
    destination = await DestinationRepository.get_destination_by_id(dest_db_session, created_dest.id)
    
    assert destination is not None
    assert destination.id == created_dest.id
    assert destination.longitude == 106.8342
    assert destination.latitude == 22.0278

@pytest.mark.asyncio
async def test_get_destination_by_coordinates(dest_db_session):
    """Test getting destination by longitude and latitude"""
    # Create destination first
    dest_data = DestinationCreate(
        longitude=107.8342,
        latitude=23.0278
    )
    created_dest = await DestinationRepository.create_destination(dest_db_session, dest_data)
    
    # Retrieve by coordinates
    destination = await DestinationRepository.get_destination_by_lon_and_lat(
        dest_db_session, 107.8342, 23.0278
    )
    
    assert destination is not None
    assert destination.id == created_dest.id
    assert destination.longitude == 107.8342
    assert destination.latitude == 23.0278

@pytest.mark.asyncio
async def test_update_destination(dest_db_session):
    """Test updating a destination"""
    # Create destination first
    dest_data = DestinationCreate(
        longitude=108.8342,
        latitude=24.0278
    )
    created_dest = await DestinationRepository.create_destination(dest_db_session, dest_data)
    
    # Update destination
    update_data = DestinationUpdate(
        longitude=109.8342,
        latitude=25.0278
    )
    updated_dest = await DestinationRepository.update_destination(
        dest_db_session, created_dest.id, update_data
    )
    
    assert updated_dest is not None
    assert updated_dest.longitude == 109.8342
    assert updated_dest.latitude == 25.0278

@pytest.mark.asyncio
async def test_delete_destination(dest_db_session):
    """Test deleting a destination"""
    # Create destination first
    dest_data = DestinationCreate(
        longitude=110.8342,
        latitude=26.0278
    )
    created_dest = await DestinationRepository.create_destination(dest_db_session, dest_data)
    
    # Delete destination
    success = await DestinationRepository.delete_destination(dest_db_session, created_dest.id)
    
    assert success is True
    
    # Verify destination is deleted
    deleted_dest = await DestinationRepository.get_destination_by_id(dest_db_session, created_dest.id)
    assert deleted_dest is None
