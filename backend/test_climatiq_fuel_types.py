"""
Test script to verify Climatiq API support for different fuel types
"""
import asyncio
from integration.climatiq_api import get_climatiq_client

async def test_climatiq_fuel_types():
    """Test Climatiq API for different fuel type queries"""
    
    print("=" * 80)
    print("🌐 TESTING CLIMATIQ API FUEL TYPE SUPPORT")
    print("=" * 80)
    
    climatiq = get_climatiq_client()
    
    if not climatiq.api_key:
        print("\n❌ No Climatiq API key found!")
        print("   Set CLIMATIQ_API_KEY in .env file")
        print("\n📋 Using fallback emission factors instead:\n")
        return
    
    # Test queries for different fuel types
    test_queries = {
        "Car - Petrol/Gasoline": [
            "passenger vehicle car petrol",
            "passenger car gasoline",
            "light duty vehicle petrol",
        ],
        "Car - Diesel": [
            "passenger vehicle car diesel",
            "passenger car diesel",
            "light duty vehicle diesel",
        ],
        "Car - Hybrid": [
            "passenger vehicle car hybrid",
            "hybrid car",
            "plug-in hybrid electric vehicle",
        ],
        "Car - Electric": [
            "passenger vehicle car electric",
            "battery electric vehicle",
            "electric car",
        ],
        "Car - CNG": [
            "passenger vehicle car cng",
            "car compressed natural gas",
            "vehicle cng",
        ],
        "Car - LPG": [
            "passenger vehicle car lpg",
            "car liquefied petroleum gas",
            "vehicle lpg",
        ],
        "Motorbike - Petrol": [
            "motorcycle petrol",
            "motorbike gasoline",
            "two wheeler petrol",
        ],
        "Motorbike - Electric": [
            "motorcycle electric",
            "electric motorbike",
            "electric two wheeler",
        ],
        "Bus - Diesel": [
            "bus diesel",
            "public transport bus diesel",
            "transit bus diesel",
        ],
        "Bus - CNG": [
            "bus cng",
            "bus compressed natural gas",
            "public transport bus cng",
        ],
        "Bus - Electric": [
            "bus electric",
            "electric bus",
            "battery electric bus",
        ],
    }
    
    results = {}
    
    for category, queries in test_queries.items():
        print(f"\n{'=' * 80}")
        print(f"🔍 Testing: {category}")
        print("-" * 80)
        
        best_result = None
        best_query = None
        
        for query in queries:
            print(f"\n   Query: '{query}'")
            search_results = await climatiq.search_emission_factors(query)
            
            if search_results:
                result = search_results[0]  # Get best match
                activity_id = result.get("activity_id", "N/A")
                name = result.get("name", "N/A")
                source = result.get("source", "N/A")
                region = result.get("region", "N/A")
                year = result.get("year", "N/A")
                unit_type = result.get("unit_type", "N/A")
                
                # Try to extract emission value
                factor = result.get("factor")
                co2e = "N/A"
                if factor and isinstance(factor, dict):
                    co2e = factor.get("co2e", "N/A")
                
                print(f"   ✅ Found: {name}")
                print(f"      Activity ID: {activity_id}")
                print(f"      Source: {source}")
                print(f"      Region: {region}")
                print(f"      Year: {year}")
                print(f"      Unit: {unit_type}")
                print(f"      CO2e Factor: {co2e}")
                
                if not best_result or (region == "VN" or region == "APAC"):
                    best_result = result
                    best_query = query
            else:
                print(f"   ❌ No results")
        
        if best_result:
            factor_data = best_result.get("factor")
            factor_value = None
            if factor_data and isinstance(factor_data, dict):
                factor_value = factor_data.get("co2e")
            
            results[category] = {
                "query": best_query,
                "activity_id": best_result.get("activity_id"),
                "name": best_result.get("name"),
                "region": best_result.get("region"),
                "factor": factor_value
            }
            print(f"\n   🏆 Best match: {best_query}")
        else:
            print(f"\n   ⚠️ No suitable results found for {category}")
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY OF CLIMATIQ API SUPPORT")
    print("=" * 80)
    
    print(f"\n✅ Found {len(results)} out of {len(test_queries)} fuel types\n")
    
    for category, data in results.items():
        print(f"✓ {category}")
        print(f"  Query: {data['query']}")
        print(f"  Activity ID: {data['activity_id']}")
        print(f"  Region: {data['region']}")
        if data['factor']:
            print(f"  Factor: {data['factor']}")
        print()
    
    # Missing fuel types
    missing = set(test_queries.keys()) - set(results.keys())
    if missing:
        print("⚠️ Missing support for:")
        for category in missing:
            print(f"  - {category}")
        print()
    
    print("=" * 80)
    print("📋 RECOMMENDATIONS")
    print("=" * 80)
    print("""
1. For fuel types NOT found in Climatiq:
   - Use fallback emission factors based on research
   - Document the source (e.g., IPCC, EPA, Vietnam MOST)
   
2. For CNG and LPG:
   - Typically 15-25% lower emissions than petrol
   - CNG: ~145 gCO2/km (car), ~58 gCO2/km (bus)
   - LPG: ~165 gCO2/km (car)
   
3. Update climatiq_api.py:
   - Add queries for CNG and LPG vehicles
   - Map results to your fuel type enum
   
4. Keep fallback factors:
   - Always maintain fallback values
   - Update periodically from research papers
    """)
    
    return results

if __name__ == "__main__":
    asyncio.run(test_climatiq_fuel_types())
