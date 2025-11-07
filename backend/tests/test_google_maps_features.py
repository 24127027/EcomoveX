import pytest
import pytest_asyncio
import httpx
from integration.google_map_api import GoogleMapsAPI, create_maps_client
import os
from dotenv import load_dotenv

load_dotenv()

@pytest_asyncio.fixture
async def maps_client():
    """Create a GoogleMapsAPI client for testing"""
    client = await create_maps_client()
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_search_places(maps_client):
    """Test search for places using text query"""
    result = await maps_client.search_places(
        query="coffee shop in Ho Chi Minh City",
        language="vi"
    )
    
    assert result.get("status") == "OK"
    assert "results" in result
    assert len(result["results"]) > 0
    print(f"\n✅ Found {len(result['results'])} coffee shops")
    print(f"First result: {result['results'][0].get('name')}")


@pytest.mark.asyncio
async def test_nearby_search(maps_client):
    """Test nearby search around a location (Bitexco Tower)"""
    result = await maps_client.nearby_search(
        lat=10.7718,
        lng=106.7017,
        radius=1000,
        type="restaurant",
        language="vi"
    )
    
    assert result.get("status") == "OK"
    assert "results" in result
    assert len(result["results"]) > 0
    print(f"\n✅ Found {len(result['results'])} restaurants near Bitexco")
    print(f"First restaurant: {result['results'][0].get('name')}")


@pytest.mark.asyncio
async def test_get_place_details(maps_client):
    """Test getting detailed place information"""
    # First search for a place to get place_id
    search_result = await maps_client.search_places(
        query="Ben Thanh Market Ho Chi Minh",
        language="vi"
    )
    
    assert search_result.get("status") == "OK"
    assert len(search_result["results"]) > 0
    
    place_id = search_result["results"][0]["place_id"]
    
    # Get place details
    result = await maps_client.get_place_details(
        place_id=place_id,
        language="vi"
    )
    
    assert result.get("status") == "OK"
    assert "result" in result
    place = result["result"]
    
    print(f"\n✅ Place details:")
    print(f"Name: {place.get('name')}")
    print(f"Address: {place.get('formatted_address')}")
    print(f"Rating: {place.get('rating')}")
    print(f"Types: {place.get('types')}")


@pytest.mark.asyncio
async def test_get_directions(maps_client):
    """Test getting directions between two locations"""
    result = await maps_client.get_directions(
        origin="Ben Thanh Market, Ho Chi Minh City",
        destination="Bitexco Tower, Ho Chi Minh City",
        mode="driving",
        language="vi"
    )
    
    assert result.get("status") == "OK"
    assert "routes" in result
    assert len(result["routes"]) > 0
    
    route = result["routes"][0]
    leg = route["legs"][0]
    
    print(f"\n✅ Directions:")
    print(f"Distance: {leg['distance']['text']}")
    print(f"Duration: {leg['duration']['text']}")
    print(f"Start: {leg['start_address']}")
    print(f"End: {leg['end_address']}")


@pytest.mark.asyncio
async def test_optimize_route(maps_client):
    """Test route optimization with multiple waypoints"""
    result = await maps_client.optimize_route(
        origin="Ben Thanh Market, Ho Chi Minh City",
        destination="Tan Son Nhat Airport, Ho Chi Minh City",
        waypoints=[
            "Bitexco Tower, Ho Chi Minh City",
            "Notre Dame Cathedral, Ho Chi Minh City",
            "War Remnants Museum, Ho Chi Minh City"
        ],
        mode="driving",
        language="vi"
    )
    
    assert result.get("status") == "OK"
    assert "routes" in result
    assert "optimized_waypoint_order" in result
    
    print(f"\n✅ Optimized route:")
    print(f"Waypoint order: {result['optimized_waypoint_order']}")
    
    route = result["routes"][0]
    total_distance = sum(leg["distance"]["value"] for leg in route["legs"])
    total_duration = sum(leg["duration"]["value"] for leg in route["legs"])
    
    print(f"Total distance: {total_distance / 1000:.2f} km")
    print(f"Total duration: {total_duration / 60:.0f} minutes")


@pytest.mark.asyncio
async def test_geocode(maps_client):
    """Test converting address to coordinates"""
    result = await maps_client.geocode(
        address="Ben Thanh Market, Ho Chi Minh City",
        language="vi"
    )
    
    assert result.get("status") == "OK"
    assert "results" in result
    assert len(result["results"]) > 0
    
    location = result["results"][0]["geometry"]["location"]
    
    print(f"\n✅ Geocoding:")
    print(f"Address: Ben Thanh Market")
    print(f"Latitude: {location['lat']}")
    print(f"Longitude: {location['lng']}")


@pytest.mark.asyncio
async def test_reverse_geocode(maps_client):
    """Test converting coordinates to address"""
    result = await maps_client.reverse_geocode(
        lat=10.7718,
        lng=106.7017,
        language="vi"
    )
    
    assert result.get("status") == "OK"
    assert "results" in result
    assert len(result["results"]) > 0
    
    print(f"\n✅ Reverse geocoding:")
    print(f"Coordinates: 10.7718, 106.7017")
    print(f"Address: {result['results'][0]['formatted_address']}")


@pytest.mark.asyncio
async def test_calculate_eco_route(maps_client):
    """Test eco-friendly route calculation"""
    result = await maps_client.calculate_eco_route(
        origin="Ben Thanh Market, Ho Chi Minh City",
        destination="Tan Son Nhat Airport, Ho Chi Minh City",
        avoid_highways=True,
        avoid_tolls=True
    )
    
    assert result.get("status") == "OK"
    assert "routes" in result
    assert len(result["routes"]) > 0
    
    route = result["routes"][0]
    
    print(f"\n✅ Eco route:")
    print(f"Distance: {route['eco_metrics']['distance_km']} km")
    print(f"Estimated CO2: {route['eco_metrics']['estimated_co2_kg']} kg")
    print(f"Duration: {route['legs'][0]['duration']['text']}")


@pytest.mark.asyncio
async def test_air_quality(maps_client):
    """Test getting air quality data"""
    result = await maps_client.get_air_quality(
        lat=10.7718,
        lng=106.7017,
        language_code="vi"
    )
    
    # Air Quality API might not be enabled or available for all locations
    # So we check for both success and error cases
    if result.get("error"):
        print(f"\n⚠️ Air Quality API error (may not be enabled): {result['error'].get('message')}")
        pytest.skip("Air Quality API not available")
    else:
        print(f"\n✅ Air quality data retrieved successfully")
        print(f"Response keys: {list(result.keys())}")


@pytest.mark.asyncio
async def test_solar_potential(maps_client):
    """Test getting solar potential data"""
    result = await maps_client.get_solar_potential(
        lat=10.7718,
        lng=106.7017
    )
    
    # Solar API might not be enabled or available for all locations
    if result.get("error"):
        print(f"\n⚠️ Solar API error (may not be enabled): {result['error'].get('message')}")
        pytest.skip("Solar API not available")
    else:
        print(f"\n✅ Solar potential data retrieved successfully")
        print(f"Response keys: {list(result.keys())}")


@pytest.mark.asyncio
async def test_pollen_forecast(maps_client):
    """Test getting pollen forecast data"""
    result = await maps_client.get_pollen_forecast(
        lat=10.7718,
        lng=106.7017,
        days=3,
        language_code="vi"
    )
    
    # Pollen API might return HTML error page instead of JSON
    if not isinstance(result, dict) or result.get("error"):
        error_msg = result.get("error", {}).get("message") if isinstance(result, dict) else "Invalid response format"
        print(f"\n⚠️ Pollen API error (may not be enabled): {error_msg}")
        pytest.skip("Pollen API not available")
    else:
        print(f"\n✅ Pollen forecast data retrieved successfully")
        print(f"Response keys: {list(result.keys())}")


@pytest.mark.asyncio
async def test_weather_forecast(maps_client):
    """Test getting weather forecast (uses reverse geocode)"""
    result = await maps_client.get_weather_forecast(
        lat=10.7718,
        lng=106.7017
    )
    
    assert "location" in result
    assert result["location"]["lat"] == 10.7718
    assert result["location"]["lng"] == 106.7017
    
    print(f"\n✅ Weather forecast:")
    print(f"Location: {result['location']['name']}")
    print(f"Message: {result['message']}")


@pytest.mark.asyncio
async def test_client_creation():
    """Test creating client with API key"""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    assert api_key is not None, "GOOGLE_MAPS_API_KEY not found in environment"
    
    client = GoogleMapsAPI(api_key=api_key)
    assert client.api_key == api_key
    assert client.base_url == "https://maps.googleapis.com/maps/api"
    
    await client.close()
    print("\n✅ Client created and closed successfully")


@pytest.mark.asyncio
async def test_client_without_api_key():
    """Test that client raises error without API key"""
    # Note: In production code, settings.GOOGLE_MAPS_API_KEY might still have a value
    # This test is skipped if the config has a default API key
    from utils.config import settings
    
    if settings.GOOGLE_MAPS_API_KEY:
        print("\n⚠️ Skipped: Config has default API key from settings")
        pytest.skip("Cannot test without API key when settings provides default")
    else:
        with pytest.raises(ValueError, match="Google Maps API key is required"):
            GoogleMapsAPI(api_key=None)
        print("\n✅ Correctly raises error without API key")
