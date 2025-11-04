import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from services.carbon_service import CarbonService
from models.carbon import VehicleType, FuelType
from schema.carbon_schema import CarbonEmissionCreate

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.fixture
def sample_emissions():
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    class MockEmission:
        def __init__(self, vehicle_type, fuel_type, distance_km, carbon_emission_kg, timestamp):
            self.vehicle_type = vehicle_type
            self.fuel_type = fuel_type
            self.distance_km = distance_km
            self.carbon_emission_kg = carbon_emission_kg
            self.timestamp = timestamp
    
    return [
        MockEmission(VehicleType.car, FuelType.petrol, 10.0, 1.71, today),
        MockEmission(VehicleType.bus, FuelType.diesel, 15.0, 1.23, today),
        MockEmission(VehicleType.car, FuelType.petrol, 20.0, 3.42, yesterday),
        MockEmission(VehicleType.motorbike, FuelType.petrol, 5.0, 0.515, yesterday),
    ]

@pytest.mark.asyncio
async def test_calculate_carbon_emission():
    emission = CarbonService.calculate_carbon_emission(
        VehicleType.car,
        10.0,
        FuelType.petrol
    )
    assert emission == 1.71
    
    emission_electric = CarbonService.calculate_carbon_emission(
        VehicleType.car,
        10.0,
        FuelType.electric
    )
    assert emission_electric == 0.53
    
    emission_walk = CarbonService.calculate_carbon_emission(
        VehicleType.walk_or_cycle,
        10.0,
        FuelType.none
    )
    assert emission_walk == 0.0

@pytest.mark.asyncio
async def test_get_total_carbon_by_day(mock_db, sample_emissions):
    with patch('repository.carbon_repository.CarbonRepository.get_carbon_emissions_by_user') as mock_get_emissions, \
         patch('integration.text_generator_api.get_text_generator') as mock_text_gen:
        
        mock_get_emissions.return_value = sample_emissions
        
        mock_generator = MagicMock()
        mock_generator.generate_text = AsyncMock(return_value="Great job! You reduced your emissions by 25% today!")
        mock_text_gen.return_value = mock_generator
        
        today = datetime.now()
        result = await CarbonService.get_total_carbon_by_day(mock_db, user_id=1, date=today)
        
        assert result["user_id"] == 1
        assert result["date"] == today.strftime("%Y-%m-%d")
        assert "summary" in result
        assert "Great job" in result["summary"]
        
        mock_get_emissions.assert_called_once_with(mock_db, 1)
        mock_generator.generate_text.assert_called_once()

@pytest.mark.asyncio
async def test_get_total_carbon_by_week(mock_db, sample_emissions):
    with patch('repository.carbon_repository.CarbonRepository.get_carbon_emissions_by_user') as mock_get_emissions, \
         patch('integration.text_generator_api.get_text_generator') as mock_text_gen:
        
        mock_get_emissions.return_value = sample_emissions
        
        mock_generator = MagicMock()
        mock_generator.generate_text = AsyncMock(return_value="This week you've made 5 trips with a total of 12.5 kg CO2.")
        mock_text_gen.return_value = mock_generator
        
        today = datetime.now()
        result = await CarbonService.get_total_carbon_by_week(mock_db, user_id=1, date=today)
        
        assert result["user_id"] == 1
        assert "week_starting" in result
        assert "week_ending" in result
        assert "summary" in result
        
        mock_generator.generate_text.assert_called_once()

@pytest.mark.asyncio
async def test_get_total_carbon_by_month(mock_db, sample_emissions):
    with patch('repository.carbon_repository.CarbonRepository.get_carbon_emissions_by_user') as mock_get_emissions, \
         patch('integration.text_generator_api.get_text_generator') as mock_text_gen:
        
        mock_get_emissions.return_value = sample_emissions
        
        mock_generator = MagicMock()
        mock_generator.generate_text = AsyncMock(return_value="Monthly summary: Your emissions decreased by 15% compared to last month!")
        mock_text_gen.return_value = mock_generator
        
        today = datetime.now()
        result = await CarbonService.get_total_carbon_by_month(mock_db, user_id=1, date=today)
        
        assert result["user_id"] == 1
        assert "month" in result
        assert "summary" in result
        assert "decreased" in result["summary"]

@pytest.mark.asyncio
async def test_get_total_carbon_by_year(mock_db, sample_emissions):
    with patch('repository.carbon_repository.CarbonRepository.get_carbon_emissions_by_user') as mock_get_emissions, \
         patch('integration.text_generator_api.get_text_generator') as mock_text_gen:
        
        mock_get_emissions.return_value = sample_emissions
        
        mock_generator = MagicMock()
        mock_generator.generate_text = AsyncMock(return_value="Yearly review: You've made great progress in reducing your carbon footprint!")
        mock_text_gen.return_value = mock_generator
        
        result = await CarbonService.get_total_carbon_by_year(mock_db, user_id=1, year=2025)
        
        assert result["user_id"] == 1
        assert result["year"] == 2025
        assert "summary" in result
        assert "progress" in result["summary"]

@pytest.mark.asyncio
async def test_prompt_contains_all_data(mock_db, sample_emissions):
    with patch('repository.carbon_repository.CarbonRepository.get_carbon_emissions_by_user') as mock_get_emissions, \
         patch('integration.text_generator_api.get_text_generator') as mock_text_gen:
        
        mock_get_emissions.return_value = sample_emissions
        
        mock_generator = MagicMock()
        mock_generator.generate_text = AsyncMock(return_value="Analysis complete")
        mock_text_gen.return_value = mock_generator
        
        today = datetime.now()
        await CarbonService.get_total_carbon_by_day(mock_db, user_id=1, date=today)
        
        call_args = mock_generator.generate_text.call_args[0][0]
        
        assert "Daily comparison" in call_args
        assert "trips" in call_args
        assert "vehicle_type" in call_args
        assert "fuel_type" in call_args
        assert "carbon_emission_kg" in call_args
        assert "Instructions:" in call_args
        assert "Calculate the total emissions" in call_args

@pytest.mark.asyncio
async def test_empty_data_handling(mock_db):
    with patch('repository.carbon_repository.CarbonRepository.get_carbon_emissions_by_user') as mock_get_emissions, \
         patch('integration.text_generator_api.get_text_generator') as mock_text_gen:
        
        mock_get_emissions.return_value = []
        
        mock_generator = MagicMock()
        mock_generator.generate_text = AsyncMock(return_value="No data available for this period.")
        mock_text_gen.return_value = mock_generator
        
        today = datetime.now()
        result = await CarbonService.get_total_carbon_by_day(mock_db, user_id=1, date=today)
        
        assert result["user_id"] == 1
        assert "summary" in result

@pytest.mark.asyncio
async def test_ai_response_formatting(mock_db, sample_emissions):
    with patch('repository.carbon_repository.CarbonRepository.get_carbon_emissions_by_user') as mock_get_emissions, \
         patch('integration.text_generator_api.get_text_generator') as mock_text_gen:
        
        mock_get_emissions.return_value = sample_emissions
        
        mock_generator = MagicMock()
        mock_generator.generate_text = AsyncMock(
            return_value="🎉 Congratulations! Your carbon emissions decreased by 30% compared to yesterday. Keep making eco-friendly choices!"
        )
        mock_text_gen.return_value = mock_generator
        
        today = datetime.now()
        result = await CarbonService.get_total_carbon_by_day(mock_db, user_id=1, date=today)
        
        assert "🎉" in result["summary"]
        assert "Congratulations" in result["summary"]
        assert "30%" in result["summary"]

if __name__ == "__main__":
    print("Running Carbon Service Tests...")
    print("\n1. Testing calculation functions...")
    import asyncio
    asyncio.run(test_calculate_carbon_emission())
    print("✅ Calculation tests passed")
    
    print("\n2. Testing daily summary with AI...")
    print("✅ All tests configured")
    print("\nRun with: pytest tests/test_carbon_service.py -v")
