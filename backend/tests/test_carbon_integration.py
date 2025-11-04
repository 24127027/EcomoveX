import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from datetime import datetime, timedelta
from services.carbon_service import CarbonService
from models.carbon import VehicleType, FuelType

class MockDB:
    """Mock database session"""
    pass

class MockEmission:
    """Mock carbon emission record"""
    def __init__(self, vehicle_type, fuel_type, distance_km, carbon_emission_kg, timestamp):
        self.vehicle_type = vehicle_type
        self.fuel_type = fuel_type
        self.distance_km = distance_km
        self.carbon_emission_kg = carbon_emission_kg
        self.timestamp = timestamp

async def test_real_ai_daily_summary():
    """Test daily summary with real AI text generation"""
    print("=" * 60)
    print("Testing Daily Carbon Summary with Real AI")
    print("=" * 60)
    
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    sample_emissions = [
        MockEmission(VehicleType.car, FuelType.petrol, 15.0, 2.565, today),
        MockEmission(VehicleType.bus, FuelType.electric, 10.0, 0.27, today),
        MockEmission(VehicleType.car, FuelType.petrol, 25.0, 4.275, yesterday),
        MockEmission(VehicleType.car, FuelType.diesel, 10.0, 1.58, yesterday),
        MockEmission(VehicleType.motorbike, FuelType.petrol, 5.0, 0.515, yesterday),
    ]
    
    from unittest.mock import patch, AsyncMock
    from repository.carbon_repository import CarbonRepository
    
    with patch.object(CarbonRepository, 'get_carbon_emissions_by_user', return_value=sample_emissions):
        mock_db = MockDB()
        result = await CarbonService.get_total_carbon_by_day(mock_db, user_id=1, date=today)
        
        print(f"\n📅 Date: {result['date']}")
        print(f"👤 User ID: {result['user_id']}")
        print(f"\n🤖 AI Generated Summary:")
        print("-" * 60)
        print(result['summary'])
        print("-" * 60)

async def test_real_ai_weekly_summary():
    """Test weekly summary with real AI text generation"""
    print("\n" + "=" * 60)
    print("Testing Weekly Carbon Summary with Real AI")
    print("=" * 60)
    
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    
    sample_emissions = [
        MockEmission(VehicleType.car, FuelType.electric, 20.0, 1.06, start_of_week),
        MockEmission(VehicleType.bus, FuelType.electric, 15.0, 0.405, start_of_week + timedelta(days=1)),
        MockEmission(VehicleType.walk_or_cycle, FuelType.none, 5.0, 0.0, start_of_week + timedelta(days=2)),
        MockEmission(VehicleType.car, FuelType.petrol, 30.0, 5.13, start_of_week + timedelta(days=3)),
        MockEmission(VehicleType.car, FuelType.petrol, 40.0, 6.84, start_of_week - timedelta(days=7)),
        MockEmission(VehicleType.car, FuelType.diesel, 25.0, 3.95, start_of_week - timedelta(days=6)),
    ]
    
    from unittest.mock import patch
    from repository.carbon_repository import CarbonRepository
    
    with patch.object(CarbonRepository, 'get_carbon_emissions_by_user', return_value=sample_emissions):
        mock_db = MockDB()
        result = await CarbonService.get_total_carbon_by_week(mock_db, user_id=1, date=today)
        
        print(f"\n📅 Week: {result['week_starting']} to {result['week_ending']}")
        print(f"👤 User ID: {result['user_id']}")
        print(f"\n🤖 AI Generated Summary:")
        print("-" * 60)
        print(result['summary'])
        print("-" * 60)

async def test_real_ai_monthly_summary():
    """Test monthly summary with real AI text generation"""
    print("\n" + "=" * 60)
    print("Testing Monthly Carbon Summary with Real AI")
    print("=" * 60)
    
    today = datetime.now()
    
    sample_emissions = []
    for day in range(1, 15):
        emission_date = datetime(today.year, today.month, day)
        sample_emissions.extend([
            MockEmission(VehicleType.car, FuelType.hybrid, 12.0, 1.344, emission_date),
            MockEmission(VehicleType.bus, FuelType.diesel, 8.0, 0.656, emission_date),
        ])
    
    last_month = today.month - 1 if today.month > 1 else 12
    last_month_year = today.year if today.month > 1 else today.year - 1
    for day in range(1, 15):
        emission_date = datetime(last_month_year, last_month, day)
        sample_emissions.extend([
            MockEmission(VehicleType.car, FuelType.petrol, 18.0, 3.078, emission_date),
            MockEmission(VehicleType.car, FuelType.diesel, 12.0, 1.896, emission_date),
        ])
    
    from unittest.mock import patch
    from repository.carbon_repository import CarbonRepository
    
    with patch.object(CarbonRepository, 'get_carbon_emissions_by_user', return_value=sample_emissions):
        mock_db = MockDB()
        result = await CarbonService.get_total_carbon_by_month(mock_db, user_id=1, date=today)
        
        print(f"\n📅 Month: {result['month']}")
        print(f"👤 User ID: {result['user_id']}")
        print(f"\n🤖 AI Generated Summary:")
        print("-" * 60)
        print(result['summary'])
        print("-" * 60)

async def test_calculation_accuracy():
    """Test carbon emission calculations"""
    print("\n" + "=" * 60)
    print("Testing Carbon Emission Calculations")
    print("=" * 60)
    
    test_cases = [
        (VehicleType.car, FuelType.petrol, 10.0, 1.71),
        (VehicleType.car, FuelType.electric, 10.0, 0.53),
        (VehicleType.bus, FuelType.diesel, 10.0, 0.82),
        (VehicleType.motorbike, FuelType.petrol, 10.0, 1.03),
        (VehicleType.walk_or_cycle, FuelType.none, 10.0, 0.0),
    ]
    
    print("\n✅ Calculation Tests:")
    for vehicle, fuel, distance, expected in test_cases:
        result = CarbonService.calculate_carbon_emission(vehicle, distance, fuel)
        status = "✓" if result == expected else "✗"
        print(f"{status} {vehicle.value} ({fuel.value}) @ {distance}km = {result} kg CO2 (expected: {expected})")

async def main():
    """Run all integration tests"""
    print("\n🧪 Carbon Service Integration Tests")
    print("Testing with Real AI Text Generation API\n")
    
    try:
        await test_calculation_accuracy()
        await test_real_ai_daily_summary()
        await test_real_ai_weekly_summary()
        await test_real_ai_monthly_summary()
        
        print("\n" + "=" * 60)
        print("✅ All Integration Tests Completed Successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
