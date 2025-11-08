"""
Test CarbonService with Climatiq API integration
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.carbon_service import CarbonService


async def test_carbon_service_with_climatiq():
    """Test CarbonService integration with Climatiq API"""
    
    print("=" * 80)
    print("🧪 CARBON SERVICE + CLIMATIQ API TEST")
    print("=" * 80)
    print()
    
    # Step 1: Show current emission factors (before refresh)
    print("Step 1: Current emission factors (hard-coded fallback)")
    print("-" * 80)
    
    current_factors = {
        "car_petrol": CarbonService.EMISSION_FACTORS_VN["car_petrol"],
        "car_diesel": CarbonService.EMISSION_FACTORS_VN["car_diesel"],
        "motorbike": CarbonService.EMISSION_FACTORS_VN["motorbike"],
        "bus_standard": CarbonService.EMISSION_FACTORS_VN["bus_standard"],
        "metro": CarbonService.EMISSION_FACTORS_VN["metro"],
    }
    
    for mode, factor in current_factors.items():
        print(f"  {mode:20s}: {factor:6.1f} gCO2/km")
    
    print()
    
    # Step 2: Refresh from Climatiq API
    print("Step 2: Refreshing from Climatiq API...")
    print("-" * 80)
    
    updated_factors = await CarbonService.refresh_emission_factors(force=True)
    
    print()
    
    # Step 3: Show updated emission factors
    print("Step 3: Updated emission factors (after Climatiq refresh)")
    print("-" * 80)
    
    for mode in current_factors.keys():
        old_value = current_factors[mode]
        new_value = CarbonService.EMISSION_FACTORS_VN[mode]
        
        if old_value == new_value:
            status = "✓ (no change)"
        else:
            change = new_value - old_value
            change_pct = (change / old_value * 100) if old_value > 0 else 0
            status = f"→ {new_value} gCO2/km ({change_pct:+.1f}%)"
        
        print(f"  {mode:20s}: {old_value:6.1f} {status}")
    
    print()
    
    # Step 4: Test emission calculation
    print("Step 4: Test emission calculation (10 km trip)")
    print("-" * 80)
    
    test_distance = 10.0
    test_modes = ["driving", "motorbike", "bus_standard", "metro", "walking"]
    
    for mode in test_modes:
        result = await CarbonService.calculate_emission_by_mode(
            distance_km=test_distance,
            mode=mode
        )
        
        icon = {"driving": "🚗", "motorbike": "🏍️", "bus_standard": "🚌", 
                "metro": "🚇", "walking": "🚶"}.get(mode, "🚗")
        
        print(f"  {icon} {mode:20s}: {result['co2e_total']:6.3f} kg CO2 "
              f"({result['emission_factor_g_per_km']:6.1f} g/km)")
    
    print()
    
    # Step 5: Test mode comparison
    print("Step 5: Compare multiple modes (5 km trip)")
    print("-" * 80)
    
    comparison = await CarbonService.compare_transport_modes(
        distance_km=5.0,
        modes=["driving", "motorbike", "transit", "bicycling"]
    )
    
    print(f"  Distance: {comparison['distance_km']} km")
    print()
    print(f"  🌱 Best option:  {comparison['best_option']['mode']:20s} = {comparison['best_option']['co2_kg']:.3f} kg CO2")
    print(f"  🔴 Worst option: {comparison['worst_option']['mode']:20s} = {comparison['worst_option']['co2_kg']:.3f} kg CO2")
    print(f"  💚 Savings potential: {comparison['savings_potential_kg']:.3f} kg CO2")
    
    print()
    
    # Step 6: Show all available factors
    print("Step 6: All available emission factors")
    print("-" * 80)
    
    all_factors = CarbonService.get_all_emission_factors()
    
    # Group by category
    categories = {
        "Private vehicles": ["car_petrol", "car_diesel", "car_hybrid", "car_electric", 
                            "motorbike", "motorbike_small", "motorbike_large"],
        "Public transport": ["bus_standard", "bus_cng", "bus_electric", "metro", 
                            "train_diesel", "train_electric"],
        "Shared/Taxi": ["taxi", "grab_car", "grab_bike"],
        "Active transport": ["bicycle", "bicycle_electric", "walking"],
    }
    
    for category, modes in categories.items():
        print(f"\n  {category}:")
        for mode in modes:
            if mode in all_factors:
                factor = all_factors[mode]
                print(f"    {mode:20s}: {factor:6.1f} gCO2/km")
    
    print()
    print("-" * 80)
    print()
    
    # Summary
    print("=" * 80)
    print("✅ CARBON SERVICE TEST COMPLETE")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  • Emission factors: {len(all_factors)} modes available")
    print(f"  • Climatiq API: {'✅ Connected' if CarbonService._factors_refreshed else '⚠️ Using fallback'}")
    print(f"  • Data source: {result['data_source']}")
    print()


if __name__ == "__main__":
    asyncio.run(test_carbon_service_with_climatiq())
