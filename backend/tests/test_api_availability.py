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
async def test_solar_api_detailed(maps_client):
    """Test Solar API with detailed error checking"""
    print("\n" + "="*60)
    print("TESTING SOLAR API")
    print("="*60)
    
    # Test multiple locations
    locations = [
        (10.7718, 106.7017, "Ho Chi Minh City, Vietnam"),
        (37.7749, -122.4194, "San Francisco, USA"),
        (40.7128, -74.0060, "New York, USA"),
    ]
    
    for lat, lng, name in locations:
        print(f"\n📍 Testing location: {name}")
        print(f"   Coordinates: {lat}, {lng}")
        
        # Direct API call to see raw response
        url = "https://solar.googleapis.com/v1/buildingInsights:findClosest"
        params = {
            "location.latitude": lat,
            "location.longitude": lng,
            "requiredQuality": "HIGH",
            "key": maps_client.api_key
        }
        
        response = await maps_client.client.get(url, params=params)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        
        try:
            data = response.json()
            print(f"   Response: {data}")
            
            if "error" in data:
                error = data["error"]
                print(f"\n   ❌ ERROR:")
                print(f"      Status: {error.get('status')}")
                print(f"      Message: {error.get('message')}")
                print(f"      Code: {error.get('code')}")
                
                # Check if it's permission or availability issue
                if error.get('status') == 'PERMISSION_DENIED':
                    print(f"      ⚠️  Reason: API KEY KHÔNG CÓ QUYỀN - Cần enable Solar API")
                elif error.get('status') == 'NOT_FOUND':
                    print(f"      ⚠️  Reason: VÙNG KHÔNG KHẢ DỤNG - Solar data chưa có cho vùng này")
                elif 'disabled' in error.get('message', '').lower():
                    print(f"      ⚠️  Reason: API CHƯA ĐƯỢC ENABLE trong Google Cloud Console")
            else:
                print(f"   ✅ SUCCESS: {data}")
        except Exception as e:
            print(f"   ❌ Parse Error: {e}")
            print(f"   Raw response: {response.text[:200]}")


@pytest.mark.asyncio
async def test_pollen_api_detailed(maps_client):
    """Test Pollen API with detailed error checking"""
    print("\n" + "="*60)
    print("TESTING POLLEN API")
    print("="*60)
    
    # Test multiple locations
    locations = [
        (10.7718, 106.7017, "Ho Chi Minh City, Vietnam"),
        (37.7749, -122.4194, "San Francisco, USA"),
        (40.7128, -74.0060, "New York, USA"),
    ]
    
    for lat, lng, name in locations:
        print(f"\n📍 Testing location: {name}")
        print(f"   Coordinates: {lat}, {lng}")
        
        # Direct API call to see raw response
        url = "https://pollen.googleapis.com/v1/forecast:lookup"
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
            params={"key": maps_client.api_key},
            json=payload
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type')}")
        
        try:
            data = response.json()
            print(f"   Response: {data}")
            
            if "error" in data:
                error = data["error"]
                print(f"\n   ❌ ERROR:")
                print(f"      Status: {error.get('status')}")
                print(f"      Message: {error.get('message')}")
                print(f"      Code: {error.get('code')}")
                
                # Check if it's permission or availability issue
                if error.get('status') == 'PERMISSION_DENIED':
                    print(f"      ⚠️  Reason: API KEY KHÔNG CÓ QUYỀN - Cần enable Pollen API")
                elif error.get('status') == 'NOT_FOUND':
                    print(f"      ⚠️  Reason: VÙNG KHÔNG KHẢ DỤNG - Pollen data chưa có cho vùng này")
                elif 'disabled' in error.get('message', '').lower():
                    print(f"      ⚠️  Reason: API CHƯA ĐƯỢC ENABLE trong Google Cloud Console")
            else:
                print(f"   ✅ SUCCESS: {list(data.keys())}")
        except Exception as e:
            print(f"   ❌ Parse Error: {e}")
            print(f"   Raw response (first 500 chars): {response.text[:500]}")


@pytest.mark.asyncio
async def test_air_quality_detailed(maps_client):
    """Test Air Quality API (which is working) for comparison"""
    print("\n" + "="*60)
    print("TESTING AIR QUALITY API (WORKING)")
    print("="*60)
    
    lat, lng = 10.7718, 106.7017
    print(f"\n📍 Testing location: Ho Chi Minh City")
    print(f"   Coordinates: {lat}, {lng}")
    
    url = "https://airquality.googleapis.com/v1/currentConditions:lookup"
    payload = {
        "location": {
            "latitude": lat,
            "longitude": lng
        },
        "languageCode": "vi"
    }
    
    response = await maps_client.client.post(
        url,
        params={"key": maps_client.api_key},
        json=payload
    )
    
    print(f"   Status Code: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('content-type')}")
    
    data = response.json()
    if "error" in data:
        print(f"   ❌ ERROR: {data['error']}")
    else:
        print(f"   ✅ SUCCESS")
        print(f"   Response keys: {list(data.keys())}")
        print(f"   DateTime: {data.get('dateTime')}")
        print(f"   Region: {data.get('regionCode')}")


@pytest.mark.asyncio
async def test_api_key_permissions():
    """Check which APIs are enabled for the API key"""
    print("\n" + "="*60)
    print("CHECKING API KEY PERMISSIONS")
    print("="*60)
    
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    print(f"\nAPI Key: {api_key[:20]}...{api_key[-10:]}")
    
    # Test different APIs with simple requests
    apis_to_test = [
        ("Geocoding API", "https://maps.googleapis.com/maps/api/geocode/json", {"address": "Ha Noi"}),
        ("Places API", "https://maps.googleapis.com/maps/api/place/textsearch/json", {"query": "restaurant"}),
        ("Directions API", "https://maps.googleapis.com/maps/api/directions/json", {"origin": "Ha Noi", "destination": "Ho Chi Minh"}),
        ("Air Quality API", "https://airquality.googleapis.com/v1/currentConditions:lookup", None),
        ("Solar API", "https://solar.googleapis.com/v1/buildingInsights:findClosest", {"location.latitude": 37.7749, "location.longitude": -122.4194}),
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("\n" + "-"*60)
        for api_name, url, params in apis_to_test:
            print(f"\n🔍 Testing: {api_name}")
            
            if params:
                params["key"] = api_key
                response = await client.get(url, params=params)
            else:
                # POST request for Air Quality
                payload = {"location": {"latitude": 10.7718, "longitude": 106.7017}}
                response = await client.post(url, params={"key": api_key}, json=payload)
            
            print(f"   Status: {response.status_code}")
            
            try:
                data = response.json()
                if "error" in data:
                    error = data["error"]
                    print(f"   ❌ {error.get('status', 'ERROR')}: {error.get('message', 'Unknown error')}")
                elif data.get("status") == "REQUEST_DENIED":
                    print(f"   ❌ REQUEST_DENIED: {data.get('error_message', 'API not enabled')}")
                elif data.get("status") == "OK" or "dateTime" in data or "name" in data:
                    print(f"   ✅ ENABLED & WORKING")
                else:
                    print(f"   ⚠️  Response: {list(data.keys())}")
            except:
                print(f"   ❌ Invalid JSON response")
