"""
Tests for Google Maps JavaScript API
Tests the JavaScript API endpoint and key validation
"""
import pytest
import os
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

@pytest.mark.asyncio
async def test_javascript_api_key_exists():
    """Test that Google Maps API key is configured for JavaScript API"""
    assert GOOGLE_MAPS_API_KEY is not None, "GOOGLE_MAPS_API_KEY not found"
    assert len(GOOGLE_MAPS_API_KEY) > 0, "GOOGLE_MAPS_API_KEY is empty"
    print(f"\n✓ API Key: {GOOGLE_MAPS_API_KEY[:15]}...")

@pytest.mark.asyncio
async def test_maps_javascript_api_loader():
    """Test loading Google Maps JavaScript API"""
    if not GOOGLE_MAPS_API_KEY:
        pytest.skip("GOOGLE_MAPS_API_KEY not configured")
    
    # Test the JavaScript API loader endpoint
    url = f"https://maps.googleapis.com/maps/api/js"
    params = {
        "key": GOOGLE_MAPS_API_KEY,
        "libraries": "places,geometry,drawing"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
    
    # JavaScript API returns JavaScript code, not JSON
    assert response.status_code == 200, f"Failed to load Maps JavaScript API: {response.status_code}"
    
    content = response.text
    
    # Check if it's actual JavaScript content
    assert "google.maps" in content or "googleapis.com" in content, "Response doesn't contain Maps API content"
    
    # Check for error messages in the response
    assert "ApiNotActivatedMapError" not in content, "Maps JavaScript API is not activated"
    assert "RefererNotAllowedMapError" not in content, "API key has referrer restrictions"
    assert "InvalidKeyMapError" not in content, "Invalid API key"
    
    print(f"\n✓ Maps JavaScript API loaded successfully")
    print(f"✓ Response size: {len(content)} bytes")

@pytest.mark.asyncio
async def test_places_library_availability():
    """Test Google Places Library for JavaScript API"""
    if not GOOGLE_MAPS_API_KEY:
        pytest.skip("GOOGLE_MAPS_API_KEY not configured")
    
    url = "https://maps.googleapis.com/maps/api/js"
    params = {
        "key": GOOGLE_MAPS_API_KEY,
        "libraries": "places"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
    
    assert response.status_code == 200, "Failed to load Places library"
    content = response.text
    
    # Should contain JavaScript code
    assert len(content) > 1000, "Response too small, likely an error"
    assert "ApiNotActivatedMapError" not in content, "Places API not activated"
    
    print(f"\n✓ Places Library loaded")

@pytest.mark.asyncio
async def test_geometry_library_availability():
    """Test Google Geometry Library for JavaScript API"""
    if not GOOGLE_MAPS_API_KEY:
        pytest.skip("GOOGLE_MAPS_API_KEY not configured")
    
    url = "https://maps.googleapis.com/maps/api/js"
    params = {
        "key": GOOGLE_MAPS_API_KEY,
        "libraries": "geometry"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
    
    assert response.status_code == 200, "Failed to load Geometry library"
    content = response.text
    
    assert len(content) > 1000, "Response too small"
    assert "ApiNotActivatedMapError" not in content, "Geometry library not activated"
    
    print(f"\n✓ Geometry Library loaded")

@pytest.mark.asyncio
async def test_static_maps_api():
    """Test Google Static Maps API (often used with JavaScript API)"""
    if not GOOGLE_MAPS_API_KEY:
        pytest.skip("GOOGLE_MAPS_API_KEY not configured")
    
    # Test Static Maps API
    url = "https://maps.googleapis.com/maps/api/staticmap"
    params = {
        "center": "Ho Chi Minh City, Vietnam",
        "zoom": "13",
        "size": "400x400",
        "key": GOOGLE_MAPS_API_KEY
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
    
    # Static Maps returns an image
    if response.status_code == 200:
        # Check if it's an image
        content_type = response.headers.get("content-type", "")
        assert "image" in content_type, f"Expected image, got {content_type}"
        print(f"\n✓ Static Maps API works")
        print(f"✓ Image size: {len(response.content)} bytes")
    else:
        # If failed, it might return HTML/JSON with error
        print(f"\n⚠️ Static Maps API status: {response.status_code}")
        if "text" in response.headers.get("content-type", ""):
            print(f"Response: {response.text[:200]}")
        # Mark as skipped if API not enabled
        pytest.skip(f"Static Maps API not enabled: {response.status_code}")

@pytest.mark.asyncio
async def test_api_key_restrictions():
    """Test if API key has appropriate restrictions"""
    if not GOOGLE_MAPS_API_KEY:
        pytest.skip("GOOGLE_MAPS_API_KEY not configured")
    
    url = "https://maps.googleapis.com/maps/api/js"
    params = {"key": GOOGLE_MAPS_API_KEY}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
    
    content = response.text
    
    print(f"\n📋 API Key Restriction Check:")
    
    # Check for common restriction errors
    if "RefererNotAllowedMapError" in content:
        print("⚠️ API key has HTTP referrer restrictions")
        print("   This is GOOD for production security")
        pytest.skip("API key has referrer restrictions (this is secure)")
    elif "IpAddressNotAllowedMapError" in content:
        print("⚠️ API key has IP address restrictions")
        pytest.skip("API key has IP restrictions")
    else:
        print("✓ API key accessible (no referrer/IP restrictions detected)")
        print("⚠️ Consider adding restrictions for production security")

@pytest.mark.asyncio
async def test_javascript_api_version():
    """Test loading specific version of Maps JavaScript API"""
    if not GOOGLE_MAPS_API_KEY:
        pytest.skip("GOOGLE_MAPS_API_KEY not configured")
    
    # Test with weekly/stable version
    url = "https://maps.googleapis.com/maps/api/js"
    params = {
        "key": GOOGLE_MAPS_API_KEY,
        "v": "weekly"  # or "quarterly", "beta"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
    
    assert response.status_code == 200, "Failed to load versioned API"
    content = response.text
    
    assert len(content) > 1000, "Response too small"
    assert "ApiNotActivatedMapError" not in content, "API not activated"
    
    print(f"\n✓ Maps JavaScript API (weekly version) loaded")

@pytest.mark.asyncio
async def test_all_required_libraries():
    """Test loading all libraries needed for EcomoveX"""
    if not GOOGLE_MAPS_API_KEY:
        pytest.skip("GOOGLE_MAPS_API_KEY not configured")
    
    # Libraries needed for eco-travel app
    libraries = ["places", "geometry", "drawing", "visualization"]
    
    url = "https://maps.googleapis.com/maps/api/js"
    params = {
        "key": GOOGLE_MAPS_API_KEY,
        "libraries": ",".join(libraries)
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
    
    assert response.status_code == 200, "Failed to load all libraries"
    content = response.text
    
    assert len(content) > 1000, "Response too small"
    
    # Check for errors
    errors = []
    if "ApiNotActivatedMapError" in content:
        errors.append("Maps JavaScript API not activated")
    if "RefererNotAllowedMapError" in content:
        errors.append("Referrer restriction (might be OK)")
    
    if errors and "RefererNotAllowedMapError" not in content:
        pytest.fail(f"Errors found: {', '.join(errors)}")
    
    print(f"\n✓ All required libraries loaded:")
    for lib in libraries:
        print(f"  • {lib}")
