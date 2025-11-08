"""
Test Climatiq API directly to see what's happening
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from integration.climatiq_api import climatiqAPI
from utils.config import settings

async def test_climatiq_direct():
    print("="*70)
    print("TESTING CLIMATIQ API DIRECTLY")
    print("="*70)
    
    print(f"\nAPI Key: {settings.CLIMATIQ_API_KEY[:10]}... (length: {len(settings.CLIMATIQ_API_KEY)})")
    
    try:
        api = climatiqAPI()
        
        # Test 1: Motorbike estimation (basic API)
        print("\n[TEST 1] Motorbike estimation (basic API endpoint)...")
        try:
            result = await api.estimate_motorbike(distance_km=10.0)
            print(f"✓ SUCCESS: CO2 = {result['co2e_total']} {result['unit']}")
        except Exception as e:
            print(f"✗ FAILED: {e}")
        
        # Test 2: Car estimation (travel API)
        print("\n[TEST 2] Car estimation (travel API endpoint)...")
        try:
            result = await api.estimate_travel_distance(
                mode="car",
                distance_km=10.0,
                passengers=1,
                fuel_type="petrol"
            )
            print(f"✓ SUCCESS: CO2 = {result['co2e_total']} {result['unit']}")
        except Exception as e:
            print(f"✗ FAILED: {e}")
        
        # Test 3: Generic transport estimation
        print("\n[TEST 3] Generic transport estimation...")
        try:
            result = await api.estimate_transport(
                mode="motorbike",
                distance_km=10.0,
                passengers=1
            )
            print(f"✓ SUCCESS: CO2 = {result['co2e_total']} {result['unit']}")
        except Exception as e:
            print(f"✗ FAILED: {e}")
        
        await api.close()
        
    except Exception as e:
        print(f"\n✗ API INITIALIZATION FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_climatiq_direct())
