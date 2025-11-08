"""
Debug script to see actual Climatiq API response structure
"""

import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from integration.climatiq_api import ClimatiqAPI

async def debug_climatiq_response():
    """Debug actual API response"""
    
    print("=" * 80)
    print("🔍 CLIMATIQ API RESPONSE DEBUG")
    print("=" * 80)
    print()
    
    client = ClimatiqAPI()
    
    if not client.api_key:
        print("❌ No API key found")
        return
    
    print("Testing search for 'passenger car'...")
    print()
    
    results = await client.search_emission_factors("passenger car")
    
    if results:
        print(f"✅ Got {len(results)} results")
        print()
        print("📋 FIRST RESULT (full structure):")
        print("-" * 80)
        print(json.dumps(results[0], indent=2))
        print("-" * 80)
    else:
        print("❌ No results")

if __name__ == "__main__":
    asyncio.run(debug_climatiq_response())