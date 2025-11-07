import pytest
import pytest_asyncio
import httpx
from integration.google_map_api import GoogleMapsAPI
import os
from dotenv import load_dotenv

load_dotenv()

@pytest_asyncio.fixture
async def maps_client():
    """Create a GoogleMapsAPI client for testing"""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    client = GoogleMapsAPI(api_key=api_key)
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_pollen_api_with_multiple_methods(maps_client):
    """Test Pollen API with different endpoints and methods"""
    print("\n" + "="*70)
    print("COMPREHENSIVE POLLEN API TEST")
    print("="*70)
    
    api_key = maps_client.api_key
    
    # Test locations
    locations = [
        (40.7128, -74.0060, "New York, USA"),
        (37.7749, -122.4194, "San Francisco, USA"),
        (10.7718, 106.7017, "Ho Chi Minh City, Vietnam"),
        (51.5074, -0.1278, "London, UK"),
    ]
    
    endpoints = [
        ("forecast:lookup", "POST", "Pollen Forecast"),
        ("currentConditions:lookup", "POST", "Current Pollen Conditions"),
        ("heatmapTiles", "GET", "Pollen Heatmap"),
    ]
    
    for endpoint, method, description in endpoints:
        print(f"\n{'='*70}")
        print(f"Testing: {description} ({method} {endpoint})")
        print(f"{'='*70}")
        
        for lat, lng, name in locations:
            print(f"\n📍 Location: {name} ({lat}, {lng})")
            
            url = f"https://pollen.googleapis.com/v1/{endpoint}"
            
            try:
                if method == "POST":
                    payload = {
                        "location": {
                            "latitude": lat,
                            "longitude": lng
                        },
                        "days": 3,
                        "languageCode": "en"
                    }
                    
                    response = await maps_client.client.post(
                        url,
                        params={"key": api_key},
                        json=payload
                    )
                else:  # GET
                    params = {
                        "key": api_key,
                        "location.latitude": lat,
                        "location.longitude": lng
                    }
                    response = await maps_client.client.get(url, params=params)
                
                print(f"   Status Code: {response.status_code}")
                print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
                
                # Try to parse as JSON
                try:
                    data = response.json()
                    
                    if "error" in data:
                        error = data["error"]
                        print(f"   ❌ ERROR:")
                        print(f"      Code: {error.get('code')}")
                        print(f"      Status: {error.get('status')}")
                        print(f"      Message: {error.get('message')}")
                        
                        # Analyze error type
                        if error.get('status') == 'PERMISSION_DENIED':
                            print(f"      ⚠️  REASON: API NOT ENABLED for this API key")
                        elif error.get('status') == 'NOT_FOUND':
                            print(f"      ⚠️  REASON: Data not available for this location")
                        elif error.get('code') == 403:
                            print(f"      ⚠️  REASON: API KEY lacks permission")
                        elif error.get('code') == 404:
                            print(f"      ⚠️  REASON: Endpoint not found (API not enabled)")
                    else:
                        print(f"   ✅ SUCCESS!")
                        print(f"   Response keys: {list(data.keys())}")
                        if 'dailyInfo' in data:
                            print(f"   Days of data: {len(data['dailyInfo'])}")
                        
                        # Show sample data
                        print(f"   Sample data: {str(data)[:200]}...")
                        
                except Exception as e:
                    print(f"   ❌ JSON Parse Error: {e}")
                    print(f"   Content (first 300 chars): {response.text[:300]}")
                    
                    # Check if it's HTML error page
                    if response.text.startswith('<!DOCTYPE html>'):
                        print(f"   ⚠️  REASON: API returned HTML error page (API NOT ENABLED)")
                    
            except Exception as e:
                print(f"   ❌ Request Error: {e}")
            
            # Small delay between requests
            import asyncio
            await asyncio.sleep(0.5)


@pytest.mark.asyncio
async def test_pollen_api_check_availability():
    """Check if Pollen API is available in Google Cloud"""
    print("\n" + "="*70)
    print("CHECKING POLLEN API AVAILABILITY")
    print("="*70)
    
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Try the simplest Pollen API call
        url = "https://pollen.googleapis.com/v1/forecast:lookup"
        
        payload = {
            "location": {
                "latitude": 37.7749,
                "longitude": -122.4194
            },
            "days": 1
        }
        
        print(f"\n🔍 Testing Pollen API with San Francisco coordinates")
        print(f"   URL: {url}")
        print(f"   Payload: {payload}")
        
        response = await client.post(
            url,
            params={"key": api_key},
            json=payload
        )
        
        print(f"\n📊 Response:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        # Analyze response
        if response.status_code == 404:
            print(f"\n❌ POLLEN API IS NOT ENABLED")
            print(f"   The API endpoint returns 404, meaning:")
            print(f"   1. Pollen API is not enabled in Google Cloud Console")
            print(f"   2. OR the API key doesn't have permission")
            print(f"\n✅ SOLUTION:")
            print(f"   1. Go to: https://console.cloud.google.com/apis/library")
            print(f"   2. Search for 'Pollen API' or 'Air Quality API'")
            print(f"   3. Click 'Enable' button")
            print(f"   4. Wait a few minutes for the API to be activated")
            
        elif response.status_code == 403:
            try:
                error_data = response.json()
                print(f"\n❌ PERMISSION DENIED")
                print(f"   Error: {error_data}")
            except:
                print(f"\n❌ PERMISSION DENIED (403)")
                print(f"   The API key doesn't have permission to access Pollen API")
                
        elif response.status_code == 200:
            try:
                data = response.json()
                print(f"\n✅ POLLEN API IS ENABLED AND WORKING!")
                print(f"   Response data: {data}")
            except:
                print(f"\n⚠️  Unexpected 200 response")
                print(f"   Content: {response.text[:500]}")
        else:
            print(f"\n⚠️  Unexpected status code: {response.status_code}")
            print(f"   Content: {response.text[:500]}")


@pytest.mark.asyncio
async def test_compare_with_air_quality():
    """Compare Pollen API with Air Quality API (which works)"""
    print("\n" + "="*70)
    print("COMPARING POLLEN API vs AIR QUALITY API")
    print("="*70)
    
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        location = {
            "latitude": 37.7749,
            "longitude": -122.4194
        }
        
        # Test Air Quality API (working)
        print(f"\n1️⃣ Testing Air Quality API (SHOULD WORK)")
        print(f"   URL: https://airquality.googleapis.com/v1/currentConditions:lookup")
        
        aq_response = await client.post(
            "https://airquality.googleapis.com/v1/currentConditions:lookup",
            params={"key": api_key},
            json={"location": location}
        )
        
        print(f"   Status: {aq_response.status_code}")
        if aq_response.status_code == 200:
            print(f"   ✅ Air Quality API WORKS")
            aq_data = aq_response.json()
            print(f"   Data keys: {list(aq_data.keys())}")
        else:
            print(f"   ❌ Unexpected: {aq_response.status_code}")
        
        # Test Pollen API
        print(f"\n2️⃣ Testing Pollen API")
        print(f"   URL: https://pollen.googleapis.com/v1/forecast:lookup")
        
        pollen_response = await client.post(
            "https://pollen.googleapis.com/v1/forecast:lookup",
            params={"key": api_key},
            json={"location": location, "days": 1}
        )
        
        print(f"   Status: {pollen_response.status_code}")
        if pollen_response.status_code == 404:
            print(f"   ❌ Pollen API NOT ENABLED (404)")
            print(f"\n🔍 CONCLUSION:")
            print(f"   - Air Quality API: ✅ ENABLED")
            print(f"   - Pollen API: ❌ NOT ENABLED")
            print(f"   - Both use the same API key")
            print(f"   - Pollen API needs to be enabled separately in Google Cloud Console")
        elif pollen_response.status_code == 200:
            print(f"   ✅ Pollen API WORKS")
            pollen_data = pollen_response.json()
            print(f"   Data keys: {list(pollen_data.keys())}")
        else:
            print(f"   ⚠️  Status: {pollen_response.status_code}")
            try:
                error_data = pollen_response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Content: {pollen_response.text[:200]}")
