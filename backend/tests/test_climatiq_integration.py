"""
Test script for Climatiq API integration

This script demonstrates how to:
1. Fetch emission factors from Climatiq API
2. Compare with hard-coded fallback values
3. Show the benefits of using real-time data
"""

import asyncio
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.carbon_service import CarbonService
from integration.climatiq_api import get_climatiq_client


async def test_climatiq_integration():
    """Test Climatiq API integration with CarbonService"""
    
    print("=" * 80)
    print("🌍 CLIMATIQ API INTEGRATION TEST")
    print("=" * 80)
    print()
    
    # Step 1: Show current (hard-coded) emission factors
    print("📋 CURRENT EMISSION FACTORS (Hard-coded fallback values):")
    print("-" * 80)
    
    current_factors = {
        "car_petrol": CarbonService.EMISSION_FACTORS_VN["car_petrol"],
        "car_diesel": CarbonService.EMISSION_FACTORS_VN["car_diesel"],
        "car_hybrid": CarbonService.EMISSION_FACTORS_VN["car_hybrid"],
        "motorbike": CarbonService.EMISSION_FACTORS_VN["motorbike"],
        "bus_standard": CarbonService.EMISSION_FACTORS_VN["bus_standard"],
        "metro": CarbonService.EMISSION_FACTORS_VN["metro"],
        "taxi": CarbonService.EMISSION_FACTORS_VN["taxi"],
    }
    
    for mode, factor in current_factors.items():
        print(f"  {mode:20s}: {factor:6.1f} gCO2/km")
    
    print()
    print("-" * 80)
    print()
    
    # Step 2: Test Climatiq API client
    print("🔌 TESTING CLIMATIQ API CONNECTION:")
    print("-" * 80)
    
    climatiq = get_climatiq_client()
    
    if not climatiq.api_key:
        print("❌ CLIMATIQ_API_KEY not found in settings")
        print()
        print("📝 TO USE CLIMATIQ API:")
        print("  1. Get free API key from: https://www.climatiq.io/")
        print("  2. Add to .env file: CLIMATIQ_API_KEY=your_key_here")
        print("  3. Restart the application")
        print()
        print("⚠️  For now, using hard-coded fallback values")
        print()
        return
    
    print(f"✅ API Key found: {climatiq.api_key[:20]}...")
    print()
    
    # Step 3: Search for sample emission factor
    print("🔍 SEARCHING CLIMATIQ DATABASE:")
    print("-" * 80)
    
    # Test search functionality
    results = await climatiq.search_emission_factors(
        query="passenger car petrol vietnam",
        region="VN"
    )
    
    if results:
        print(f"✅ Found {len(results)} results for 'passenger car petrol vietnam'")
        print()
        print("  Sample result:")
        result = results[0]
        print(f"    Name: {result.get('name', 'N/A')}")
        print(f"    Factor: {result.get('factor', {}).get('value', 0)} {result.get('factor', {}).get('unit', '')}")
        print(f"    Source: {result.get('source', 'N/A')}")
        print(f"    Year: {result.get('year', 'N/A')}")
    else:
        print("⚠️  No results found (may need valid API key)")
    
    print()
    print("-" * 80)
    print()
    
    # Step 4: Refresh all emission factors
    print("🔄 REFRESHING EMISSION FACTORS FROM CLIMATIQ API:")
    print("-" * 80)
    
    updated_factors = await CarbonService.refresh_emission_factors(force=True)
    
    print()
    print("-" * 80)
    print()
    
    # Step 5: Compare before and after
    print("📊 COMPARISON: Hard-coded vs Climatiq API:")
    print("-" * 80)
    print(f"{'Mode':<20} {'Hard-coded':>12} {'Climatiq API':>12} {'Change':>10}")
    print("-" * 80)
    
    for mode in current_factors.keys():
        old_value = current_factors[mode]
        new_value = updated_factors.get(mode, old_value)
        change = new_value - old_value
        change_pct = (change / old_value * 100) if old_value > 0 else 0
        
        change_str = f"{change:+.0f} ({change_pct:+.1f}%)"
        print(f"{mode:<20} {old_value:>12.1f} {new_value:>12.1f} {change_str:>10}")
    
    print()
    print("-" * 80)
    print()
    
    # Step 6: Test emission calculation with updated factors
    print("🚗 EMISSION CALCULATION WITH UPDATED FACTORS:")
    print("-" * 80)
    
    distance = 10.0  # km
    test_modes = ["driving", "motorbike", "bus_standard", "metro"]
    
    print(f"Trip distance: {distance} km")
    print()
    
    for mode in test_modes:
        result = await CarbonService.calculate_emission_by_mode(
            distance_km=distance,
            mode=mode
        )
        
        print(f"  {result['mode']:20s}: {result['co2e_total']:.3f} kg CO2 ({result['emission_factor_g_per_km']:.0f} g/km)")
    
    print()
    print("-" * 80)
    print()
    
    # Step 7: Benefits summary
    print("✨ BENEFITS OF USING CLIMATIQ API:")
    print("-" * 80)
    print("  ✅ Always up-to-date emission factors")
    print("  ✅ Scientifically verified data from multiple sources")
    print("  ✅ Regular updates as emission standards change")
    print("  ✅ Country/region-specific accuracy")
    print("  ✅ No manual updates needed")
    print("  ✅ 24-hour caching reduces API calls")
    print()
    print("  📚 Data sources:")
    print("     - IPCC (Intergovernmental Panel on Climate Change)")
    print("     - IEA (International Energy Agency)")
    print("     - National greenhouse gas inventories")
    print("     - Academic research papers")
    print()
    print("-" * 80)
    print()
    
    print("=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)


async def main():
    """Main entry point"""
    try:
        await test_climatiq_integration()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
