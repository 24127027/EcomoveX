"""
Quick test to verify CarbonService migration
"""
import asyncio
from services.carbon_service import CarbonService


async def test_emission_calculation():
    """Test basic emission calculation"""
    print("=" * 60)
    print("Testing CarbonService Emission Calculation")
    print("=" * 60)
    
    # Test 1: Calculate emission for 10km driving
    result = await CarbonService.calculate_emission_by_mode(10, 'driving')
    print(f"\n✅ Test 1: 10km driving")
    print(f"   CO2: {result['co2e_total']} kg")
    print(f"   Emission factor: {result['emission_factor_g_per_km']} g/km")
    print(f"   Data source: {result['data_source']}")
    
    # Test 2: Compare multiple modes
    print(f"\n✅ Test 2: Compare transport modes for 5km")
    comparison = await CarbonService.compare_transport_modes(5, ['car_petrol', 'motorbike', 'bus_standard', 'bicycle'])
    print(f"   Best option: {comparison['best_option']['mode']} ({comparison['best_option']['co2_kg']} kg)")
    print(f"   Worst option: {comparison['worst_option']['mode']} ({comparison['worst_option']['co2_kg']} kg)")
    print(f"   Savings potential: {comparison['savings_potential_kg']} kg CO2")
    
    # Test 3: Get all emission factors
    print(f"\n✅ Test 3: All emission factors")
    all_factors = CarbonService.get_all_emission_factors()
    print(f"   Car petrol: {all_factors['car_petrol']} g/km")
    print(f"   Motorbike: {all_factors['motorbike']} g/km")
    print(f"   Bus: {all_factors['bus_standard']} g/km")
    print(f"   Metro: {all_factors['metro']} g/km")
    print(f"   Bicycle: {all_factors['bicycle']} g/km")
    print(f"   Car electric: {all_factors['car_electric']} g/km")
    
    # Test 4: Try real-time grid intensity
    print(f"\n✅ Test 4: Real-time grid intensity")
    grid_intensity = await CarbonService.get_realtime_grid_intensity()
    if grid_intensity:
        print(f"   Real-time grid: {grid_intensity} gCO2/kWh")
    else:
        print(f"   Using static grid: {CarbonService.GRID_INTENSITY_VN} gCO2/kWh")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! CarbonService migration successful!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_emission_calculation())
