"""
Test script to verify enum integration in carbon_service.py
This script tests that the refactored carbon service using enums from models.route
still calculates emissions correctly for all fuel types and transport modes.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.carbon_service import CarbonService
from models.route import TransportMode, FuelType

async def test_enum_integration():
    """Test that enum integration maintains correct emission calculations"""
    
    print("=" * 80)
    print("Testing Enum Integration in Carbon Service")
    print("=" * 80)
    
    test_distance = 10.0  # 10 km for all tests
    
    # Test 1: Car with all fuel types
    print("\n1. Testing Car with All Fuel Types")
    print("-" * 80)
    
    car_fuel_tests = [
        (FuelType.PETROL.value, 192),
        (FuelType.GASOLINE.value, 192),
        (FuelType.DIESEL.value, 171),
        (FuelType.HYBRID.value, 120),
        (FuelType.ELECTRIC.value, 103.8),  # 0.20 kWh/km * 519 gCO2/kWh
        (FuelType.CNG.value, 145),
        (FuelType.LPG.value, 165),
    ]
    
    for fuel_type, expected_factor in car_fuel_tests:
        result = await CarbonService.calculate_emission_by_mode(
            distance_km=test_distance,
            mode=TransportMode.car.value,
            fuel_type=fuel_type,
            passengers=1
        )
        
        print(f"  {fuel_type.upper():12} - Factor: {result.emission_factor_g_per_km:6.1f} gCO2/km "
              f"(expected: {expected_factor:6.1f}) - "
              f"Total: {result.total_co2_kg:.3f} kg")
        
        # Allow small tolerance for electric vehicles due to grid intensity calculation
        tolerance = 2.0 if fuel_type == FuelType.ELECTRIC.value else 0.1
        assert abs(result.emission_factor_g_per_km - expected_factor) < tolerance, \
            f"Factor mismatch for {fuel_type}: got {result.emission_factor_g_per_km}, expected {expected_factor}"
    
    # Test 2: Different transport modes with default fuel
    print("\n2. Testing Different Transport Modes (Default Fuel)")
    print("-" * 80)
    
    mode_tests = [
        (TransportMode.car.value, None, 192),
        (TransportMode.motorbike.value, None, 84),
        (TransportMode.bus.value, None, 68),
        (TransportMode.taxi.value, None, 155),
        (TransportMode.bicycle.value, None, 0),
        (TransportMode.walking.value, None, 0),
        (TransportMode.metro.value, None, 35),
    ]
    
    for mode, fuel_type, expected_factor in mode_tests:
        result = await CarbonService.calculate_emission_by_mode(
            distance_km=test_distance,
            mode=mode,
            fuel_type=fuel_type,
            passengers=1
        )
        
        print(f"  {mode:15} - Factor: {result.emission_factor_g_per_km:6.1f} gCO2/km "
              f"(expected: {expected_factor:6.1f}) - "
              f"Total: {result.total_co2_kg:.3f} kg")
        
        assert abs(result.emission_factor_g_per_km - expected_factor) < 0.1, \
            f"Factor mismatch for {mode}: got {result.emission_factor_g_per_km}, expected {expected_factor}"
    
    # Test 3: MODE_MAPPING with aliases
    print("\n3. Testing MODE_MAPPING Aliases")
    print("-" * 80)
    
    alias_tests = [
        ("driving", FuelType.DIESEL.value, 171),  # driving -> car
        ("motorcycle", FuelType.ELECTRIC.value, 15.57),  # motorcycle -> motorbike electric (0.03 kWh/km * 519 gCO2/kWh)
        ("transit", FuelType.CNG.value, 58),  # transit -> bus
        ("subway", None, 35),  # subway -> metro
        ("bicycling", None, 0),  # bicycling -> bicycle
    ]
    
    for alias, fuel_type, expected_factor in alias_tests:
        result = await CarbonService.calculate_emission_by_mode(
            distance_km=test_distance,
            mode=alias,
            fuel_type=fuel_type,
            passengers=1
        )
        
        fuel_str = f"({fuel_type})" if fuel_type else "(default)"
        print(f"  {alias:15} {fuel_str:12} - Factor: {result.emission_factor_g_per_km:6.1f} gCO2/km "
              f"(expected: {expected_factor:6.1f})")
        
        tolerance = 2.0 if fuel_type == FuelType.ELECTRIC.value else 0.1
        assert abs(result.emission_factor_g_per_km - expected_factor) < tolerance, \
            f"Factor mismatch for alias {alias}: got {result.emission_factor_g_per_km}, expected {expected_factor}"
    
    # Test 4: Traffic multiplier with different fuel types
    print("\n4. Testing Traffic Multiplier with Different Fuel Types")
    print("-" * 80)
    
    congestion_ratio = 1.5  # Moderate traffic
    
    traffic_tests = [
        (TransportMode.car.value, FuelType.PETROL.value),
        (TransportMode.car.value, FuelType.DIESEL.value),
        (TransportMode.car.value, FuelType.HYBRID.value),
        (TransportMode.motorbike.value, FuelType.PETROL.value),
        (TransportMode.taxi.value, FuelType.HYBRID.value),
    ]
    
    for mode, fuel_type in traffic_tests:
        # Without traffic
        result_no_traffic = await CarbonService.calculate_emission_by_mode(
            distance_km=test_distance,
            mode=mode,
            fuel_type=fuel_type,
            passengers=1,
            congestion_ratio=1.0
        )
        
        # With traffic
        result_with_traffic = await CarbonService.calculate_emission_by_mode(
            distance_km=test_distance,
            mode=mode,
            fuel_type=fuel_type,
            passengers=1,
            congestion_ratio=congestion_ratio
        )
        
        increase_pct = ((result_with_traffic.emission_factor_g_per_km / result_no_traffic.emission_factor_g_per_km) - 1) * 100
        
        print(f"  {mode:15} ({fuel_type:8}) - "
              f"No Traffic: {result_no_traffic.emission_factor_g_per_km:6.1f} gCO2/km, "
              f"With Traffic: {result_with_traffic.emission_factor_g_per_km:6.1f} gCO2/km "
              f"(+{increase_pct:.1f}%)")
        
        # Traffic should increase emissions for motorized vehicles
        assert result_with_traffic.emission_factor_g_per_km > result_no_traffic.emission_factor_g_per_km, \
            f"Traffic should increase emissions for {mode} {fuel_type}"
    
    # Test 5: Electric bicycle
    print("\n5. Testing Special Cases (Electric Bicycle)")
    print("-" * 80)
    
    result_regular_bike = await CarbonService.calculate_emission_by_mode(
        distance_km=test_distance,
        mode=TransportMode.bicycle.value,
        fuel_type=None,
        passengers=1
    )
    
    result_electric_bike = await CarbonService.calculate_emission_by_mode(
        distance_km=test_distance,
        mode=TransportMode.bicycle.value,
        fuel_type=FuelType.ELECTRIC.value,
        passengers=1
    )
    
    print(f"  Regular Bicycle  - Factor: {result_regular_bike.emission_factor_g_per_km:6.1f} gCO2/km")
    print(f"  Electric Bicycle - Factor: {result_electric_bike.emission_factor_g_per_km:6.1f} gCO2/km")
    
    assert result_regular_bike.emission_factor_g_per_km == 0, "Regular bicycle should have 0 emissions"
    assert result_electric_bike.emission_factor_g_per_km > 0, "Electric bicycle should have some emissions from grid"
    
    # Test 6: Verify enum usage in EMISSION_FACTORS_VN
    print("\n6. Verifying Enum-Based Dictionary Keys")
    print("-" * 80)
    
    expected_keys = [
        f"{TransportMode.car.value}_{FuelType.PETROL.value}",
        f"{TransportMode.car.value}_{FuelType.DIESEL.value}",
        f"{TransportMode.motorbike.value}_{FuelType.ELECTRIC.value}",
        f"{TransportMode.bus.value}_{FuelType.CNG.value}",
        TransportMode.metro.value,
        TransportMode.walking.value,
    ]
    
    for key in expected_keys:
        assert key in CarbonService.EMISSION_FACTORS_VN, f"Key '{key}' should exist in EMISSION_FACTORS_VN"
        print(f"  ✓ Key exists: {key}")
    
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED!")
    print("=" * 80)
    print("\nSummary:")
    print("  ✓ All fuel types calculate correctly with enum values")
    print("  ✓ Transport mode enums work correctly")
    print("  ✓ MODE_MAPPING aliases resolve to enum values")
    print("  ✓ Traffic multiplier applies to enum-based modes")
    print("  ✓ Special cases (electric bicycle) work correctly")
    print("  ✓ Dictionary keys use enum values as expected")
    print("\nEnum integration successful! No regressions detected.")

if __name__ == "__main__":
    asyncio.run(test_enum_integration())
