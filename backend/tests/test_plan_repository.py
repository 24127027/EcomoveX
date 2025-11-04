# Test Plan Repository and Service
import pytest
from datetime import date
from repository.plan_repository import PlanRepository
from repository.user_repository import UserRepository
from repository.destination_repository import DestinationRepository
from schema.plan_schema import PlanRequestCreate, PlanRequestUpdate
from schema.authentication_schema import UserRegister
from schema.destination_schema import DestinationCreate
from models.plan import DestinationType

@pytest.mark.asyncio
async def test_create_plan(user_db_session):
    """Test creating a new plan"""
    # Create user first
    user_data = UserRegister(
        username="planuser",
        email="plan@example.com",
        password="hashedpassword123"
    )
    user = await UserRepository.create_user(user_db_session, user_data)
    
    # Create plan
    plan_data = PlanRequestCreate(
        place_name="Hanoi Trip",
        start_date=date(2025, 12, 1),
        end_date=date(2025, 12, 10),
        budget_limit=5000.0
    )
    
    plan = await PlanRepository.create_plan(user_db_session, user.id, plan_data)
    
    assert plan is not None
    assert plan.user_id == user.id
    assert plan.place_name == "Hanoi Trip"
    assert plan.budget_limit == 5000.0

@pytest.mark.asyncio
async def test_get_plan_by_user(user_db_session):
    """Test getting plans by user ID"""
    # Create user
    user_data = UserRegister(
        username="planuser2",
        email="plan2@example.com",
        password="hashedpassword123"
    )
    user = await UserRepository.create_user(user_db_session, user_data)
    
    # Create multiple plans
    plan_data1 = PlanRequestCreate(
        place_name="Trip 1",
        start_date=date(2025, 12, 1),
        end_date=date(2025, 12, 5),
        budget_limit=2000.0
    )
    await PlanRepository.create_plan(user_db_session, user.id, plan_data1)
    
    plan_data2 = PlanRequestCreate(
        place_name="Trip 2",
        start_date=date(2025, 12, 10),
        end_date=date(2025, 12, 15),
        budget_limit=3000.0
    )
    await PlanRepository.create_plan(user_db_session, user.id, plan_data2)
    
    # Get plans
    plans = await PlanRepository.get_plan_by_user_id(user_db_session, user.id)
    
    assert plans is not None
    assert len(plans) == 2
    assert all(plan.user_id == user.id for plan in plans)

@pytest.mark.asyncio
async def test_add_destination_to_plan(user_db_session, dest_db_session):
    """Test adding a destination to a plan (cross-database operation)"""
    # Create user
    user_data = UserRegister(
        username="planuser3",
        email="plan3@example.com",
        password="hashedpassword123"
    )
    user = await UserRepository.create_user(user_db_session, user_data)
    
    # Create plan
    plan_data = PlanRequestCreate(
        place_name="Hanoi Adventure",
        start_date=date(2025, 12, 1),
        end_date=date(2025, 12, 10),
        budget_limit=5000.0
    )
    plan = await PlanRepository.create_plan(user_db_session, user.id, plan_data)
    
    # Create destination in destination DB
    dest_data = DestinationCreate(
        name="Hoan Kiem Lake",
        longitude=105.8526,
        latitude=21.0285
    )
    destination = await DestinationRepository.create_destination(dest_db_session, dest_data)
    
    # Add destination to plan
    plan_dest = await PlanRepository.add_destination_to_plan(
        user_db_session,
        plan.id,
        destination.id,
        DestinationType.attraction,
        date(2025, 12, 2),
        "Visit in the morning"
    )
    
    assert plan_dest is not None
    assert plan_dest.plan_id == plan.id
    assert plan_dest.destination_id == destination.id
    assert plan_dest.type == DestinationType.attraction
    assert plan_dest.note == "Visit in the morning"

@pytest.mark.asyncio
async def test_get_plan_destinations(user_db_session, dest_db_session):
    """Test getting all destinations for a plan"""
    # Create user
    user_data = UserRegister(
        username="planuser4",
        email="plan4@example.com",
        password="hashedpassword123"
    )
    user = await UserRepository.create_user(user_db_session, user_data)
    
    # Create plan
    plan_data = PlanRequestCreate(
        place_name="Multi-Stop Trip",
        start_date=date(2025, 12, 1),
        end_date=date(2025, 12, 10),
        budget_limit=5000.0
    )
    plan = await PlanRepository.create_plan(user_db_session, user.id, plan_data)
    
    # Create destinations
    dest1_data = DestinationCreate(name="Location 1", longitude=105.1, latitude=21.1)
    dest1 = await DestinationRepository.create_destination(dest_db_session, dest1_data)
    
    dest2_data = DestinationCreate(name="Location 2", longitude=105.2, latitude=21.2)
    dest2 = await DestinationRepository.create_destination(dest_db_session, dest2_data)
    
    # Add destinations to plan
    await PlanRepository.add_destination_to_plan(
        user_db_session, plan.id, dest1.id, DestinationType.hotel, date(2025, 12, 1)
    )
    await PlanRepository.add_destination_to_plan(
        user_db_session, plan.id, dest2.id, DestinationType.restaurant, date(2025, 12, 2)
    )
    
    # Get plan destinations
    plan_destinations = await PlanRepository.get_plan_destinations(user_db_session, plan.id)
    
    assert len(plan_destinations) == 2
    assert all(pd.plan_id == plan.id for pd in plan_destinations)

@pytest.mark.asyncio
async def test_update_plan(user_db_session):
    """Test updating a plan"""
    # Create user
    user_data = UserRegister(
        username="planuser5",
        email="plan5@example.com",
        password="hashedpassword123"
    )
    user = await UserRepository.create_user(user_db_session, user_data)
    
    # Create plan
    plan_data = PlanRequestCreate(
        place_name="Original Trip",
        start_date=date(2025, 12, 1),
        end_date=date(2025, 12, 5),
        budget_limit=2000.0
    )
    plan = await PlanRepository.create_plan(user_db_session, user.id, plan_data)
    
    # Update plan
    update_data = PlanRequestUpdate(
        place_name="Updated Trip",
        budget_limit=3000.0
    )
    updated_plan = await PlanRepository.update_plan(user_db_session, plan.id, update_data)
    
    assert updated_plan is not None
    assert updated_plan.place_name == "Updated Trip"
    assert updated_plan.budget_limit == 3000.0

@pytest.mark.asyncio
async def test_delete_plan(user_db_session):
    """Test deleting a plan"""
    # Create user
    user_data = UserRegister(
        username="planuser6",
        email="plan6@example.com",
        password="hashedpassword123"
    )
    user = await UserRepository.create_user(user_db_session, user_data)
    
    # Create plan
    plan_data = PlanRequestCreate(
        place_name="To Delete",
        start_date=date(2025, 12, 1),
        end_date=date(2025, 12, 5),
        budget_limit=2000.0
    )
    plan = await PlanRepository.create_plan(user_db_session, user.id, plan_data)
    
    # Delete plan
    success = await PlanRepository.delete_plan(user_db_session, plan.id)
    
    assert success is True
    
    # Verify deleted
    plans = await PlanRepository.get_plan_by_user_id(user_db_session, user.id)
    assert len(plans) == 0
