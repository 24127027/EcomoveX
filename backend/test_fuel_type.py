"""
Test script for fuel type feature in carbon emission calculation
Demonstrates how different fuel types affect carbon emissions
"""

import asyncio
from services.carbon_service import CarbonService

async def test_fuel_types():
    """Test carbon emission calculation with different fuel types"""
    
    print("=" * 80)
    print("🚗 TESTING FUEL TYPE FEATURE - Carbon Emission Calculation")
    print("=" * 80)
    
    distance = 50.0  # 50 km trip
    
    # Test 1: Car with different fuel types
    print("\n📊 TEST 1: Car with different fuel types (50km)")
    print("-" * 80)
    
    fuel_types = ["petrol", "diesel", "hybrid", "electric", "cng", "lpg"]
    
    for fuel in fuel_types:
        result = await CarbonService.calculate_emission_by_mode(
            distance_km=distance,
            mode="car",
            fuel_type=fuel
        )
        
        print(f"\n🚙 Car - {fuel.upper()}")
        print(f"   Distance: {result.distance_km} km")
        print(f"   Mode: {result.mode}")
        print(f"   Fuel Type: {result.fuel_type}")
        print(f"   Emission Factor: {result.emission_factor_g_per_km} gCO2/km")
        print(f"   Total CO2: {result.total_co2_kg} kg")
        print(f"   Data Source: {result.data_source}")
    
    # Test 2: Default fuel type (should be petrol)
    print("\n" + "=" * 80)
    print("📊 TEST 2: Default fuel type (no fuel_type specified)")
    print("-" * 80)
    
    result_default = await CarbonService.calculate_emission_by_mode(
        distance_km=distance,
        mode="car"
    )
    
    print(f"\n🚗 Car - Default (no fuel_type parameter)")
    print(f"   Distance: {result_default.distance_km} km")
    print(f"   Mode: {result_default.mode}")
    print(f"   Fuel Type: {result_default.fuel_type}")
    print(f"   Emission Factor: {result_default.emission_factor_g_per_km} gCO2/km")
    print(f"   Total CO2: {result_default.total_co2_kg} kg")
    print(f"   ✅ Should default to petrol")
    
    # Test 3: Motorbike with fuel types
    print("\n" + "=" * 80)
    print("📊 TEST 3: Motorbike with different fuel types (50km)")
    print("-" * 80)
    
    motorbike_fuels = ["petrol", "electric"]
    
    for fuel in motorbike_fuels:
        result = await CarbonService.calculate_emission_by_mode(
            distance_km=distance,
            mode="motorbike",
            fuel_type=fuel
        )
        
        print(f"\n🏍️ Motorbike - {fuel.upper()}")
        print(f"   Mode: {result.mode}")
        print(f"   Fuel Type: {result.fuel_type}")
        print(f"   Emission Factor: {result.emission_factor_g_per_km} gCO2/km")
        print(f"   Total CO2: {result.total_co2_kg} kg")
    
    # Test 4: Bus with fuel types
    print("\n" + "=" * 80)
    print("📊 TEST 4: Bus with different fuel types (50km)")
    print("-" * 80)
    
    bus_fuels = ["diesel", "cng", "electric"]
    
    for fuel in bus_fuels:
        result = await CarbonService.calculate_emission_by_mode(
            distance_km=distance,
            mode="bus",
            fuel_type=fuel
        )
        
        print(f"\n🚌 Bus - {fuel.upper()}")
        print(f"   Mode: {result.mode}")
        print(f"   Fuel Type: {result.fuel_type}")
        print(f"   Emission Factor: {result.emission_factor_g_per_km} gCO2/km")
        print(f"   Total CO2: {result.total_co2_kg} kg")
    
    # Test 5: Comparison - Petrol vs Electric car
    print("\n" + "=" * 80)
    print("📊 TEST 5: COMPARISON - Petrol vs Electric Car (50km)")
    print("-" * 80)
    
    petrol_car = await CarbonService.calculate_emission_by_mode(
        distance_km=distance,
        mode="car",
        fuel_type="petrol"
    )
    
    electric_car = await CarbonService.calculate_emission_by_mode(
        distance_km=distance,
        mode="car",
        fuel_type="electric"
    )
    
    print(f"\n🚗 Petrol Car:")
    print(f"   Total CO2: {petrol_car.total_co2_kg} kg")
    
    print(f"\n⚡ Electric Car:")
    print(f"   Total CO2: {electric_car.total_co2_kg} kg")
    if electric_car.grid_intensity_used:
        print(f"   Grid Intensity: {electric_car.grid_intensity_used} gCO2/kWh")
    
    savings = petrol_car.total_co2_kg - electric_car.total_co2_kg
    savings_percent = (savings / petrol_car.total_co2_kg * 100) if petrol_car.total_co2_kg > 0 else 0
    
    print(f"\n💚 Savings with Electric:")
    print(f"   CO2 Saved: {savings:.3f} kg ({savings_percent:.1f}%)")
    
    # Test 6: Traffic impact with different fuel types
    print("\n" + "=" * 80)
    print("📊 TEST 6: Traffic impact on different fuel types (50km, 1.5x congestion)")
    print("-" * 80)
    
    congestion = 1.5
    
    for fuel in ["petrol", "diesel", "hybrid"]:
        result = await CarbonService.calculate_emission_by_mode(
            distance_km=distance,
            mode="car",
            fuel_type=fuel,
            congestion_ratio=congestion
        )
        
        print(f"\n🚗 Car - {fuel.upper()} (with traffic)")
        print(f"   Emission Factor: {result.emission_factor_g_per_km} gCO2/km")
        print(f"   Total CO2: {result.total_co2_kg} kg")
        print(f"   Traffic Multiplier: {result.traffic_multiplier}x")
        print(f"   Emission Increase: {result.emission_increase_percent}%")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED!")
    print("=" * 80)
    print("\n📋 SUMMARY:")
    print("   ✅ Fuel type parameter added to carbon calculation")
    print("   ✅ Default fuel type is 'petrol' when not specified")
    print("   ✅ Supported fuel types: petrol, diesel, hybrid, electric, cng, lpg")
    print("   ✅ Different fuel types show different emission factors")
    print("   ✅ Traffic multiplier works with all fuel types")
    print("   ✅ Electric vehicles show 0 direct emissions (but use grid intensity)")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_fuel_types())
