# Test Carbon Repository
import pytest
from datetime import datetime
from repository.carbon_repository import CarbonRepository
from repository.user_repository import UserRepository
from schema.carbon_schema import CarbonEmissionCreate
from schema.authentication_schema import UserRegister
from models.carbon import VehicleType, FuelType

@pytest.mark.asyncio
async def test_create_carbon_emission(user_db_session):
    """Test creating a carbon emission record"""
    # Create user first
    user_data = UserRegister(
        username="carbonuser",
        email="carbon@example.com",
        password="hashedpassword123"
    )
    user = await UserRepository.create_user(user_db_session, user_data)
    
    # Create carbon emission
    emission_data = CarbonEmissionCreate(
        vehicle_type=VehicleType.car,
        distance_km=10.5,
        fuel_type=FuelType.petrol
    )
    
    emission = await CarbonRepository.create_carbon_emission(
        user_db_session, user.id, emission_data, 2.5
    )
    
    assert emission is not None
    assert emission.user_id == user.id
    assert emission.vehicle_type == VehicleType.car
    assert emission.distance_km == 10.5
    assert emission.fuel_type == FuelType.petrol
    assert emission.carbon_emission_kg == 2.5

@pytest.mark.asyncio
async def test_get_carbon_emissions_by_user(user_db_session):
    """Test getting all carbon emissions for a user"""
    # Create user
    user_data = UserRegister(
        username="carbonuser2",
        email="carbon2@example.com",
        password="hashedpassword123"
    )
    user = await UserRepository.create_user(user_db_session, user_data)
    
    # Create multiple emissions
    emission_data1 = CarbonEmissionCreate(
        vehicle_type=VehicleType.car,
        distance_km=10.0,
        fuel_type=FuelType.petrol
    )
    await CarbonRepository.create_carbon_emission(user_db_session, user.id, emission_data1, 2.0)
    
    emission_data2 = CarbonEmissionCreate(
        vehicle_type=VehicleType.bus,
        distance_km=20.0,
        fuel_type=FuelType.diesel
    )
    await CarbonRepository.create_carbon_emission(user_db_session, user.id, emission_data2, 3.0)
    
    # Get all emissions
    emissions = await CarbonRepository.get_carbon_emissions_by_user(user_db_session, user.id)
    
    assert len(emissions) == 2
    assert emissions[0].user_id == user.id
    assert emissions[1].user_id == user.id

@pytest.mark.asyncio
async def test_get_total_carbon_by_user(user_db_session):
    """Test calculating total carbon emissions for a user"""
    # Create user
    user_data = UserRegister(
        username="carbonuser3",
        email="carbon3@example.com",
        password="hashedpassword123"
    )
    user = await UserRepository.create_user(user_db_session, user_data)
    
    # Create emissions
    emission_data1 = CarbonEmissionCreate(
        vehicle_type=VehicleType.car,
        distance_km=10.0,
        fuel_type=FuelType.petrol
    )
    await CarbonRepository.create_carbon_emission(user_db_session, user.id, emission_data1, 5.0)
    
    emission_data2 = CarbonEmissionCreate(
        vehicle_type=VehicleType.bus,
        distance_km=20.0,
        fuel_type=FuelType.diesel
    )
    await CarbonRepository.create_carbon_emission(user_db_session, user.id, emission_data2, 3.5)
    
    # Get total
    total = await CarbonRepository.get_total_carbon_by_user(user_db_session, user.id)
    
    assert total == 8.5

@pytest.mark.asyncio
async def test_delete_carbon_emission(user_db_session):
    """Test deleting a carbon emission"""
    # Create user
    user_data = UserRegister(
        username="carbonuser4",
        email="carbon4@example.com",
        password="hashedpassword123"
    )
    user = await UserRepository.create_user(user_db_session, user_data)
    
    # Create emission
    emission_data = CarbonEmissionCreate(
        vehicle_type=VehicleType.car,
        distance_km=10.0,
        fuel_type=FuelType.petrol
    )
    emission = await CarbonRepository.create_carbon_emission(
        user_db_session, user.id, emission_data, 2.0
    )
    
    # Delete emission
    success = await CarbonRepository.delete_carbon_emission(
        user_db_session, emission.id, user.id
    )
    
    assert success is True
    
    # Verify deleted
    deleted_emission = await CarbonRepository.get_carbon_emission_by_id(
        user_db_session, emission.id, user.id
    )
    assert deleted_emission is None
