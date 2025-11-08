import httpx
from typing import Dict, List, Optional, Any, Tuple
from utils.config import settings
import math
from schemas.map_schema import (
    SearchLocationRequest,
    DirectionsResponse,
    GeocodingResponse,
    AutocompleteResponse,
    PlaceDetailsResponse
)
from models.route import TransportMode

class GoogleMapsAPI:   
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GOOGLE_MAPS_API_KEY
        if not self.api_key:
            raise ValueError("Google Maps API key is required")
        
        self.base_url = "https://maps.googleapis.com/maps/api"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        await self.client.aclose()

    async def autocomplete_place(self, data: SearchLocationRequest, components: str = "country:vn") -> AutocompleteResponse:
        """Search for places using autocomplete with Pydantic response"""
        params = {
            "input": data.query.strip(),
            "language": data.language,
            "key": self.api_key
        }

        if data.user_location:
            params["location"] = f"{data.user_location[0]},{data.user_location[1]}"
        if data.radius:
            params["radius"] = data.radius
        if data.place_types:
            params["types"] = data.place_types
        if components:
            params["components"] = components
        
        url = f"{self.base_url}/place/autocomplete/json"
        response = await self.client.get(url, params=params)
        return AutocompleteResponse(**response.json())

    async def query_autocomplete(self, data: SearchLocationRequest) -> AutocompleteResponse:
        params = {
            "input": data.query.strip(),
            "language": data.language,
            "key": self.api_key
        }

        if data.user_location:
            params["location"] = f"{data.user_location[0]},{data.user_location[1]}"
        if data.radius:
            params["radius"] = data.radius

        url = f"{self.base_url}/place/queryautocomplete/json"
        response = await self.client.get(url, params=params)
        return AutocompleteResponse(**response.json())

    async def get_place_details_from_autocomplete(self, place_id: str, fields: Optional[List[str]] = None, language: str = "vi") -> PlaceDetailsResponse:
        """Get detailed place information with Pydantic response"""
        if fields is None:
            fields = [
                "place_id",
                "name", 
                "formatted_address",
                "geometry/location",
                "address_components",
                "rating",
                "opening_hours",
                "formatted_phone_number",
                "website",
                "photos",
                "types"
            ]
        
        params = {
            "place_id": place_id,
            "fields": ",".join(fields),
            "language": language,
            "key": self.api_key
        }
        
        url = f"{self.base_url}/place/details/json"
        response = await self.client.get(url, params=params)
        return PlaceDetailsResponse(**response.json())
    
    async def get_directions(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        mode: TransportMode,
        waypoints: Optional[List[str]] = None,
        alternatives: bool = False,
        avoid: Optional[List[str]] = None,
        language: str = "vi"
    ) -> DirectionsResponse:
        """Get directions between locations with Pydantic response"""
        params = {
            "origin": f"{origin[0]},{origin[1]}",
            "destination": f"{destination[0]},{destination[1]}",
            "mode": mode.value,
            "alternatives": str(alternatives).lower(),
            "language": language,
            "key": self.api_key
        }
        
        if waypoints:
            params["waypoints"] = "optimize:true|" + "|".join(waypoints)
        if avoid:
            params["avoid"] = "|".join(avoid)
        
        url = f"{self.base_url}/directions/json"
        response = await self.client.get(url, params=params)
        return DirectionsResponse(**response.json())
    
    async def get_air_quality(
        self,
        lat: float,
        lng: float,
        language_code: str = "vi"
    ) -> Dict[str, Any]:
        """Get current air quality data"""
        payload = {
            "location": {
                "latitude": lat,
                "longitude": lng
            },
            "languageCode": language_code
        }
        
        url = "https://airquality.googleapis.com/v1/currentConditions:lookup"
        response = await self.client.post(
            url,
            params={"key": self.api_key},
            json=payload
        )
        return response.json()
    
    async def get_air_quality_history(
        self,
        lat: float,
        lng: float,
        hours: int = 24,
        language_code: str = "vi"
    ) -> Dict[str, Any]:
        """Get historical air quality data"""
        payload = {
            "location": {
                "latitude": lat,
                "longitude": lng
            },
            "hours": hours,
            "languageCode": language_code
        }
        
        url = "https://airquality.googleapis.com/v1/history:lookup"
        response = await self.client.post(
            url,
            params={"key": self.api_key},
            json=payload
        )
        return response.json()
    
    async def get_air_quality_with_pollutants(
        self,
        lat: float,
        lng: float,
        extra_computations: Optional[List[str]] = None,
        language_code: str = "vi"
    ) -> Dict[str, Any]:
        payload = {
            "location": {
                "latitude": lat,
                "longitude": lng
            },
            "languageCode": language_code
        }
        
        if extra_computations:
            payload["extraComputations"] = extra_computations
        
        url = "https://airquality.googleapis.com/v1/currentConditions:lookup"
        response = await self.client.post(
            url,
            params={"key": self.api_key},
            json=payload
        )
        return response.json()
    
    async def get_air_quality_heatmap(
        self,
        lat: float,
        lng: float,
        zoom: int = 12
    ) -> Dict[str, Any]:
        n = 2.0 ** zoom
        x = int((lng + 180.0) / 360.0 * n)
        y = int((1.0 - math.log(math.tan(math.radians(lat)) + (1 / math.cos(math.radians(lat)))) / math.pi) / 2.0 * n)
        
        url = f"https://airquality.googleapis.com/v1/mapTypes/UAQI_RED_GREEN/heatmapTiles/{zoom}/{x}/{y}"
        response = await self.client.get(url, params={"key": self.api_key})
        
        return {
            "tile_url": url,
            "zoom": zoom,
            "x": x,
            "y": y,
            "location": {"lat": lat, "lng": lng},
            "status_code": response.status_code
        }
        
    async def get_weather_forecast(
        self,
        lat: float,
        lng: float
    ) -> Dict[str, Any]:
        """Get weather forecast (uses geocoding + external weather API)"""
        geocode_result = await self.reverse_geocode(lat, lng)
        
        location_name = "Unknown"
        if geocode_result.get("status") == "OK" and geocode_result.get("results"):
            location_name = geocode_result["results"][0].get("formatted_address", "Unknown")
        
        return {
            "location": {
                "lat": lat,
                "lng": lng,
                "name": location_name
            },
            "message": "Use external weather API like OpenWeatherMap for detailed forecast"
        }
    
    async def get_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        mode: TransportMode,
    ) -> DirectionsResponse:
        """Get single route between locations with Pydantic response"""
        params = {
            "origin": f"{origin[0]},{origin[1]}",
            "destination": f"{destination[0]},{destination[1]}",
            "mode": mode.value,
            "key": self.api_key
        }
        
        url = f"{self.base_url}/directions/json"
        response = await self.client.get(url, params=params)
        return DirectionsResponse(**response.json())
    
    async def reverse_geocode(
        self,
        lat: float,
        lng: float,
        language: str = "vi"
    ) -> GeocodingResponse:
        """Convert coordinates to address with Pydantic response"""
        params = {
            "latlng": f"{lat},{lng}",
            "language": language,
            "key": self.api_key
        }
        
        url = f"{self.base_url}/geocode/json"
        response = await self.client.get(url, params=params)
        return GeocodingResponse(**response.json())
    
    async def geocode(
        self,
        address: str,
        language: str = "vi",
        region: str = "vn"
    ) -> GeocodingResponse:
        """Convert address to coordinates with Pydantic response"""
        params = {
            "address": address,
            "language": language,
            "region": region,
            "key": self.api_key
        }
        
        url = f"{self.base_url}/geocode/json"
        response = await self.client.get(url, params=params)
        return GeocodingResponse(**response.json())
    
    def _extract_transit_details(self, leg: Dict[str, Any]) -> Dict[str, Any]:
        """Extract transit step details (bus/train lines, stops, etc.)"""
        transit_steps = []
        walking_steps = []
        
        for step in leg.get("steps", []):
            if step.get("travel_mode") == "TRANSIT":
                transit_details = step.get("transit_details", {})
                transit_steps.append({
                    "line": transit_details.get("line", {}).get("short_name", "N/A"),
                    "vehicle": transit_details.get("line", {}).get("vehicle", {}).get("type", "BUS"),
                    "departure_stop": transit_details.get("departure_stop", {}).get("name", ""),
                    "arrival_stop": transit_details.get("arrival_stop", {}).get("name", ""),
                    "num_stops": transit_details.get("num_stops", 0),
                    "duration": step.get("duration", {}).get("text", "")
                })
            elif step.get("travel_mode") == "WALKING":
                walking_steps.append({
                    "distance": step.get("distance", {}).get("text", ""),
                    "duration": step.get("duration", {}).get("text", ""),
                    "instruction": step.get("html_instructions", "")
                })
        
        return {
            "transit_steps": transit_steps,
            "walking_steps": walking_steps,
            "total_transit_steps": len(transit_steps),
            "total_walking_steps": len(walking_steps)
        }

async def create_maps_client(api_key: Optional[str] = None) -> GoogleMapsAPI:
    return GoogleMapsAPI(api_key=api_key)