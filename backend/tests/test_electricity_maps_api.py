"""Quick test for Electricity Maps API"""
import asyncio
from services.carbon_service import CarbonService
from utils.config import settings


async def test_api():
    print("="*80)
    print("Testing Electricity Maps API")
    print("="*80)
    
    api_key = settings.ELECTRICCITYMAPS_API_KEY if hasattr(settings, 'ELECTRICCITYMAPS_API_KEY') else None
    print(f"API Key: {'✅ ' + api_key[:10] + '...' if api_key else '❌ Not found'}")
    print(f"Default grid intensity: {CarbonService.GRID_INTENSITY_VN} gCO2/kWh")
    print()
    
    print("Fetching real-time data for Vietnam...")
    intensity = await CarbonService.get_realtime_grid_intensity("VN")
    
    if intensity:
        print(f"✅ SUCCESS!")
        print(f"Real-time intensity: {intensity} gCO2/kWh")
        print(f"Difference from default: {intensity - CarbonService.GRID_INTENSITY_VN:+.1f} gCO2/kWh ({((intensity - CarbonService.GRID_INTENSITY_VN) / CarbonService.GRID_INTENSITY_VN * 100):.1f}%)")
        print()
        
        # Calculate EV emissions with real-time data
        print("Electric vehicle emissions with real-time grid:")
        for mode, efficiency in CarbonService.EV_EFFICIENCY.items():
            emission = efficiency * intensity
            default_emission = efficiency * CarbonService.GRID_INTENSITY_VN
            print(f"  {mode:20s}: {emission:.1f} gCO2/km (was {default_emission:.1f})")
    else:
        print("❌ Failed to fetch real-time data")
        print("Using default grid intensity")


if __name__ == "__main__":
    asyncio.run(test_api())
