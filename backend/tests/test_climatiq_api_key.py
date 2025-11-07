"""
Quick test for Climatiq API - Just to check if API key works

Run this after you get your Climatiq API key and add it to .env
"""

import asyncio
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from integration.climatiq_api import ClimatiqAPI
from utils.config import settings


async def test_climatiq_api_key():
    """Quick test to verify Climatiq API key works"""
    
    print("=" * 80)
    print("🔑 CLIMATIQ API KEY TEST")
    print("=" * 80)
    print()
    
    # Step 1: Check if API key exists
    print("Step 1: Checking for API key...")
    print("-" * 80)
    
    api_key = getattr(settings, 'CLIMATIQ_API_KEY', None)
    
    if not api_key:
        print("❌ CLIMATIQ_API_KEY not found in .env file")
        print()
        print("📝 TO GET API KEY:")
        print("  1. Go to: https://www.climatiq.io/")
        print("  2. Sign up (FREE - no credit card needed)")
        print("  3. Copy your API key from dashboard")
        print("  4. Add to .env file:")
        print("     CLIMATIQ_API_KEY=your_key_here")
        print()
        print("  Read: HOW_TO_GET_CLIMATIQ_API_KEY.md for detailed guide")
        print()
        return False
    
    print(f"✅ API Key found: {api_key[:20]}...")
    print()
    
    # Step 2: Test API connection
    print("Step 2: Testing API connection...")
    print("-" * 80)
    
    client = ClimatiqAPI(api_key=api_key)
    
    # Try a simple search
    try:
        results = await client.search_emission_factors(
            query="passenger car",
            region="VN"
        )
        
        if results:
            print(f"✅ SUCCESS! API is working")
            print(f"   Found {len(results)} emission factors for 'passenger car'")
            print()
            print("   Sample result:")
            sample = results[0]
            print(f"     Name: {sample.get('name', 'N/A')}")
            print(f"     Activity ID: {sample.get('activity_id', 'N/A')}")
            print(f"     Unit: {sample.get('unit', 'N/A')}")
            print(f"     Source: {sample.get('source', 'N/A')}")
            print(f"     Year: {sample.get('year', 'N/A')}")
            print(f"     Region: {sample.get('region', 'N/A')}")
            print()
            return True
        else:
            print("⚠️  API returned no results (but connection works)")
            print("    This might be normal if no data for Vietnam")
            print()
            return True
            
    except Exception as e:
        print(f"❌ API Error: {e}")
        print()
        print("Possible issues:")
        print("  - Invalid API key")
        print("  - Network connection problem")
        print("  - API rate limit exceeded")
        print()
        return False
    
    print()


async def test_fetch_vietnam_factors():
    """Test fetching all Vietnam transport factors"""
    
    print("Step 3: Fetching Vietnam transport emission factors...")
    print("-" * 80)
    
    client = ClimatiqAPI()
    
    if not client.api_key:
        print("⚠️  Skipping (no API key)")
        return
    
    try:
        factors = await client.get_vietnam_transport_factors(use_cache=False)
        
        if factors:
            print(f"✅ Successfully fetched {len(factors)} emission factors!")
            print()
            print("📊 Vietnam Transport Emission Factors:")
            print("-" * 80)
            
            for mode, factor in sorted(factors.items()):
                if factor > 0:
                    print(f"  {mode:20s}: {factor:6.1f} gCO2/km")
            
            print()
            print("Zero-emission modes:")
            for mode, factor in sorted(factors.items()):
                if factor == 0:
                    print(f"  {mode:20s}: {factor:6.1f} gCO2/km")
            
            print()
        else:
            print("⚠️  No factors retrieved")
            print("   Using fallback hard-coded values")
            print()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print()


async def main():
    """Main entry point"""
    
    success = await test_climatiq_api_key()
    
    if success:
        print()
        await test_fetch_vietnam_factors()
        print()
        print("=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        print()
        print("📚 Next steps:")
        print("  1. API key is working correctly")
        print("  2. You can now enable auto-refresh in main.py")
        print("  3. Read: integration/CLIMATIQ_INTEGRATION_GUIDE.md")
        print()
    else:
        print()
        print("=" * 80)
        print("❌ TEST FAILED")
        print("=" * 80)
        print()
        print("📝 Please get your FREE API key:")
        print("   1. Visit: https://www.climatiq.io/")
        print("   2. Sign up (no credit card needed)")
        print("   3. Get API key from dashboard")
        print("   4. Add to .env: CLIMATIQ_API_KEY=your_key")
        print("   5. Run this test again")
        print()
        print("📖 Read: HOW_TO_GET_CLIMATIQ_API_KEY.md")
        print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
