"""
Tests for Google Maps API integration

⚠️ IMPORTANT: These tests require Google Maps APIs to be enabled in Google Cloud Console:
   1. Geocoding API
   2. Places API  
   3. Directions API
   4. Distance Matrix API

Current Status: API key exists but APIs not enabled
Error: "This API project is not authorized to use this API."

To enable APIs:
1. Go to https://console.cloud.google.com/
2. Select your project
3. Go to "APIs & Services" > "Library"
4. Search for and enable each required API
"""
import pytest
import os
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

@pytest.mark.asyncio
async def test_google_maps_api_key_exists():
    """Test that Google Maps API key is configured"""
    assert GOOGLE_MAPS_API_KEY is not None, "GOOGLE_MAPS_API_KEY not found in environment"
    assert len(GOOGLE_MAPS_API_KEY) > 0, "GOOGLE_MAPS_API_KEY is empty"
    print(f"\n✓ API Key found: {GOOGLE_MAPS_API_KEY[:10]}...")

@pytest.mark.asyncio
async def test_google_maps_api_error_details():
    """Test Google Maps API and show detailed error message"""
    if not GOOGLE_MAPS_API_KEY:
        pytest.skip("GOOGLE_MAPS_API_KEY not configured")
    
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": "Vietnam",
        "key": GOOGLE_MAPS_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
    
    data = response.json()
    
    print(f"\nAPI Response Status: {data.get('status')}")
    if 'error_message' in data:
        print(f"Error Message: {data['error_message']}")
    
    print(f"\nFull Response: {data}")
    
    # This test documents the API state rather than asserting success
    if data["status"] == "REQUEST_DENIED":
        pytest.skip(f"API Key issue: {data.get('error_message', 'REQUEST_DENIED')}")
    
    assert data["status"] in ["OK", "ZERO_RESULTS"], f"Unexpected status: {data['status']}"

@pytest.mark.asyncio
async def test_google_maps_geocoding_api():
    """Test Google Maps Geocoding API with the configured key"""
    if not GOOGLE_MAPS_API_KEY:
        pytest.skip("GOOGLE_MAPS_API_KEY not configured")
    
    # Test geocoding a well-known address
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": "Ho Chi Minh City, Vietnam",
        "key": GOOGLE_MAPS_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        
    assert response.status_code == 200, f"API request failed with status {response.status_code}"
    
    data = response.json()
    
    # Skip if API key has issues
    if data["status"] == "REQUEST_DENIED":
        pytest.skip(f"API Key not enabled for Geocoding API: {data.get('error_message', '')}")
    
    assert data["status"] == "OK", f"API returned status: {data['status']}"
    assert len(data["results"]) > 0, "No results returned from API"
    assert "geometry" in data["results"][0], "No geometry data in response"
    
    # Verify location data
    location = data["results"][0]["geometry"]["location"]
    assert "lat" in location, "No latitude in response"
    assert "lng" in location, "No longitude in response"

@pytest.mark.asyncio
async def test_google_maps_places_api():
    """Test Google Maps Places API nearby search"""
    if not GOOGLE_MAPS_API_KEY:
        pytest.skip("GOOGLE_MAPS_API_KEY not configured")
    
    # Test nearby search for a location in Ho Chi Minh City
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": "10.8231,106.6297",  # Ho Chi Minh City coordinates
        "radius": 1000,
        "type": "tourist_attraction",
        "key": GOOGLE_MAPS_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
    
    assert response.status_code == 200, f"API request failed with status {response.status_code}"
    
    data = response.json()
    
    # Skip if API key has issues
    if data["status"] == "REQUEST_DENIED":
        pytest.skip(f"API Key not enabled for Places API: {data.get('error_message', '')}")
    
    # Places API might return OK, ZERO_RESULTS, or other statuses
    assert data["status"] in ["OK", "ZERO_RESULTS"], f"API returned unexpected status: {data['status']}"
    
    if data["status"] == "OK":
        assert "results" in data, "No results field in response"
        # If there are results, verify structure
        if len(data["results"]) > 0:
            place = data["results"][0]
            assert "name" in place, "No name in place data"
            assert "geometry" in place, "No geometry in place data"

@pytest.mark.asyncio
async def test_google_maps_directions_api():
    """Test Google Maps Directions API"""
    if not GOOGLE_MAPS_API_KEY:
        pytest.skip("GOOGLE_MAPS_API_KEY not configured")
    
    # Test directions between two points in Ho Chi Minh City
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": "Ben Thanh Market, Ho Chi Minh City",
        "destination": "Notre-Dame Cathedral, Ho Chi Minh City",
        "mode": "driving",
        "key": GOOGLE_MAPS_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
    
    assert response.status_code == 200, f"API request failed with status {response.status_code}"
    
    data = response.json()
    
    # Skip if API key has issues
    if data["status"] == "REQUEST_DENIED":
        pytest.skip(f"API Key not enabled for Directions API: {data.get('error_message', '')}")
    
    assert data["status"] == "OK", f"API returned status: {data['status']}"
    assert len(data["routes"]) > 0, "No routes returned from API"
    
    # Verify route data
    route = data["routes"][0]
    assert "legs" in route, "No legs in route data"
    assert len(route["legs"]) > 0, "No legs data in route"
    
    leg = route["legs"][0]
    assert "distance" in leg, "No distance in leg data"
    assert "duration" in leg, "No duration in leg data"

@pytest.mark.asyncio
async def test_google_maps_distance_matrix_api():
    """Test Google Maps Distance Matrix API"""
    if not GOOGLE_MAPS_API_KEY:
        pytest.skip("GOOGLE_MAPS_API_KEY not configured")
    
    # Test distance matrix for carbon calculation
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": "10.7769,106.7009",  # District 1, HCMC
        "destinations": "10.8231,106.6297",  # Tan Binh, HCMC
        "mode": "driving",
        "key": GOOGLE_MAPS_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
    
    assert response.status_code == 200, f"API request failed with status {response.status_code}"
    
    data = response.json()
    
    # Skip if API key has issues
    if data["status"] == "REQUEST_DENIED":
        pytest.skip(f"API Key not enabled for Distance Matrix API: {data.get('error_message', '')}")
    
    assert data["status"] == "OK", f"API returned status: {data['status']}"
    assert "rows" in data, "No rows in response"
    assert len(data["rows"]) > 0, "No rows data"
    
    # Verify distance data
    elements = data["rows"][0]["elements"]
    assert len(elements) > 0, "No elements in response"
    
    element = elements[0]
    if element["status"] == "OK":
        assert "distance" in element, "No distance in element"
        assert "duration" in element, "No duration in element"
        assert "value" in element["distance"], "No distance value"

@pytest.mark.asyncio
async def test_google_maps_api_key_validity():
    """Test if the API key is valid and not expired"""
    if not GOOGLE_MAPS_API_KEY:
        pytest.skip("GOOGLE_MAPS_API_KEY not configured")
    
    # Simple geocoding test to verify key validity
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": "Vietnam",
        "key": GOOGLE_MAPS_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
    
    data = response.json()
    
    # Skip if API not enabled
    if data["status"] == "REQUEST_DENIED":
        pytest.skip(f"API not enabled or restricted: {data.get('error_message', 'REQUEST_DENIED')}")
    
    # Check for common error statuses
    assert data["status"] != "INVALID_REQUEST", "Invalid request - check API key configuration"
    assert data["status"] in ["OK", "ZERO_RESULTS"], f"Unexpected API status: {data['status']}"

@pytest.mark.asyncio
async def test_google_maps_api_quota():
    """Test that API has available quota (makes a simple request)"""
    if not GOOGLE_MAPS_API_KEY:
        pytest.skip("GOOGLE_MAPS_API_KEY not configured")
    
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "latlng": "10.8231,106.6297",
        "key": GOOGLE_MAPS_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
    
    data = response.json()
    
    # Skip if API not enabled
    if data["status"] == "REQUEST_DENIED":
        pytest.skip(f"API not enabled: {data.get('error_message', 'REQUEST_DENIED')}")
    
    # Check for quota-related errors
    assert data["status"] != "OVER_QUERY_LIMIT", "API quota exceeded"
    assert data["status"] != "OVER_DAILY_LIMIT", "Daily API quota exceeded"
    assert data["status"] in ["OK", "ZERO_RESULTS"], f"API status: {data['status']}"
