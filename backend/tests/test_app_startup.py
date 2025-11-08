"""
Test app startup with auto-refresh emission factors
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.carbon_service import CarbonService


async def simulate_app_startup():
    """Simulate FastAPI app startup event"""
    
    print("=" * 80)
    print("🚀 SIMULATING APP STARTUP")
    print("=" * 80)
    print()
    
    # Simulate startup sequence
    print("🚀 Starting EcomoveX Backend...")
    print()
    
    # Database initialization (simulated)
    print("✅ Main database initialized")
    print("✅ Destination database initialized")
    print()
    
    # Auto-refresh emission factors
    try:
        print("🌍 Loading latest emission factors from Climatiq API...")
        await CarbonService.refresh_emission_factors()
        print("✅ Emission factors loaded successfully")
    except Exception as e:
        print(f"⚠️  Emission factors refresh failed (using fallback values): {e}")
    
    print()
    print("-" * 80)
    print()
    
    # Verify emission factors are loaded
    print("📊 CURRENT EMISSION FACTORS:")
    print("-" * 80)
    
    factors = CarbonService.get_all_emission_factors()
    
    categories = {
        "Private vehicles": ["car_petrol", "car_diesel", "car_hybrid", "car_electric", "motorbike"],
        "Public transport": ["bus_standard", "bus_cng", "metro", "train_diesel"],
        "Active transport": ["bicycle", "walking"],
    }
    
    for category, modes in categories.items():
        print(f"\n{category}:")
        for mode in modes:
            if mode in factors:
                factor = factors[mode]
                print(f"  {mode:20s}: {factor:6.1f} gCO2/km")
    
    print()
    print("-" * 80)
    print()
    
    # Test emission calculation
    print("🧪 TESTING EMISSION CALCULATION:")
    print("-" * 80)
    
    test_distance = 5.0
    result = await CarbonService.calculate_emission_by_mode(
        distance_km=test_distance,
        mode="driving"
    )
    
    print(f"  Distance: {test_distance} km")
    print(f"  Mode: driving")
    print(f"  Emission: {result['co2e_total']} kg CO2")
    print(f"  Factor: {result['emission_factor_g_per_km']} g/km")
    print(f"  Source: {result['data_source']}")
    
    print()
    print("=" * 80)
    print("✅ APP STARTUP COMPLETE")
    print("=" * 80)
    print()
    
    status_icon = "✅" if CarbonService._factors_refreshed else "⚠️"
    status_text = "Climatiq API" if CarbonService._factors_refreshed else "Fallback values"
    
    print(f"{status_icon} Emission factors source: {status_text}")
    print(f"📊 Total modes available: {len(factors)}")
    print()


if __name__ == "__main__":
    asyncio.run(simulate_app_startup())
