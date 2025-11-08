"""
Simplified test to check Climatiq API fuel type support
"""
import asyncio
from integration.climatiq_api import get_climatiq_client

async def check_climatiq_support():
    """Quick check of Climatiq API fuel type support"""
    
    print("=" * 80)
    print("CLIMATIQ API FUEL TYPE SUPPORT CHECK")
    print("=" * 80)
    
    climatiq = get_climatiq_client()
    
    if not climatiq.api_key:
        print("\nNo Climatiq API key found!")
        print("Using fallback emission factors from research.\n")
        print("=" * 80)
        print("FALLBACK EMISSION FACTORS (gCO2/km)")
        print("=" * 80)
        print("\nCar fuel types:")
        print("  - Petrol/Gasoline: 192 (Source: IPCC 2019, Vietnam MOST 2020)")
        print("  - Diesel: 171 (Source: IPCC 2019)")
        print("  - Hybrid: 120 (Source: EPA 2020)")
        print("  - Electric: 103.8 (0 direct + 519 grid * 0.2 kWh/km)")
        print("  - CNG: 145 (Source: EPA 2020, 25% lower than petrol)")
        print("  - LPG: 165 (Source: EPA 2020, 14% lower than petrol)")
        print("\nMotorbike fuel types:")
        print("  - Petrol: 84 (Source: Vietnam MOST 2020)")
        print("  - Electric: 15.57 (0 direct + 519 grid * 0.03 kWh/km)")
        print("\nBus fuel types:")
        print("  - Diesel: 68 (Source: IPCC 2019)")
        print("  - CNG: 58 (Source: EPA 2020)")
        print("  - Electric: 674.7 (0 direct + 519 grid * 1.3 kWh/km)")
        print("\n" + "=" * 80)
        return
    
    print("\nClimatiq API key found. Testing queries...")
    print("-" * 80)
    
    # Test key fuel types
    test_queries = {
        "Car Petrol": "passenger vehicle car petrol",
        "Car Diesel": "passenger vehicle car diesel", 
        "Car Hybrid": "hybrid car",
        "Car Electric": "electric car",
        "Car CNG": "vehicle cng",
        "Car LPG": "vehicle lpg",
        "Motorbike Petrol": "motorcycle petrol",
        "Bus Diesel": "bus diesel",
        "Bus CNG": "bus cng",
    }
    
    found_count = 0
    
    for name, query in test_queries.items():
        results = await climatiq.search_emission_factors(query)
        if results:
            result = results[0]
            activity_id = result.get("activity_id", "N/A")
            region = result.get("region", "N/A")
            print(f"  OK {name:20s} - Found: {activity_id[:50]}... (Region: {region})")
            found_count += 1
        else:
            print(f"  -- {name:20s} - No results (using fallback)")
    
    print("-" * 80)
    print(f"\nFound {found_count}/{len(test_queries)} fuel types in Climatiq")
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print("""
The application uses a hybrid approach:
1. Try to fetch from Climatiq API (if API key available)
2. Fall back to research-based emission factors

Current fallback factors are based on:
- IPCC 2019 Guidelines
- US EPA 2020-2023 data
- Vietnam Ministry of Science & Technology 2020
- European Environment Agency 2019

This ensures the app works even without Climatiq API access.
""")

if __name__ == "__main__":
    asyncio.run(check_climatiq_support())
