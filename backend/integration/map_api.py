"""
Google Maps API Integration
Provides access to Google Maps Platform APIs:
- Places API (search nearby places, place details)
- Geocoding API (convert addresses to coordinates)
- Directions API (calculate routes and travel times)
- Distance Matrix API (calculate distances between points)
"""

import httpx
from typing import Optional, List, Dict, Any
from utils.config import settings


class GoogleMapsClient:
    """
    Client for Google Maps Platform APIs.
    
    Supports:
    - Places Search (nearby, text search, place details)
    - Geocoding (address to coordinates)
    - Reverse Geocoding (coordinates to address)
    - Directions (route planning)
    - Distance Matrix (travel time/distance calculations)
    """
    
    BASE_URL = "https://maps.googleapis.com/maps/api"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key from settings or parameter."""
        self.api_key = api_key or settings.GOOGLE_MAPS_API_KEY
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    # ==================== PLACES API ====================
    
    async def search_nearby_places(
        self,
        latitude: float,
        longitude: float,
        radius: int = 5000,
        place_type: Optional[str] = None,
        keyword: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Search for places near a location.
        
        Args:
            latitude: Center point latitude
            longitude: Center point longitude
            radius: Search radius in meters (max 50000)
            place_type: Type of place (restaurant, hotel, tourist_attraction, etc.)
            keyword: Search term
            min_price: Minimum price level (0-4)
            max_price: Maximum price level (0-4)
        
        Returns:
            Dictionary with 'results' containing list of places
        """
        url = f"{self.BASE_URL}/place/nearbysearch/json"
        
        params = {
            "location": f"{latitude},{longitude}",
            "radius": radius,
            "key": self.api_key,
        }
        
        if place_type:
            params["type"] = place_type
        if keyword:
            params["keyword"] = keyword
        if min_price is not None:
            params["minprice"] = min_price
        if max_price is not None:
            params["maxprice"] = max_price
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    async def search_places_by_text(
        self,
        query: str,
        location: Optional[tuple[float, float]] = None,
        radius: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Search for places using a text query.
        
        Args:
            query: Text search query (e.g., "vegan restaurants in Paris")
            location: Optional (latitude, longitude) to bias results
            radius: Optional search radius in meters
        
        Returns:
            Dictionary with 'results' containing list of places
        """
        url = f"{self.BASE_URL}/place/textsearch/json"
        
        params = {
            "query": query,
            "key": self.api_key,
        }
        
        if location:
            params["location"] = f"{location[0]},{location[1]}"
        if radius:
            params["radius"] = radius
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_place_details(
        self,
        place_id: str,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific place.
        
        Args:
            place_id: Google Place ID
            fields: List of fields to return (e.g., ["name", "rating", "formatted_address"])
        
        Returns:
            Dictionary with 'result' containing place details
        """
        url = f"{self.BASE_URL}/place/details/json"
        
        params = {
            "place_id": place_id,
            "key": self.api_key,
        }
        
        if fields:
            params["fields"] = ",".join(fields)
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    # ==================== GEOCODING API ====================
    
    async def geocode_address(self, address: str) -> Dict[str, Any]:
        """
        Convert an address to geographic coordinates.
        
        Args:
            address: Address string to geocode
        
        Returns:
            Dictionary with 'results' containing coordinates and formatted address
        """
        url = f"{self.BASE_URL}/geocode/json"
        
        params = {
            "address": address,
            "key": self.api_key,
        }
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    async def reverse_geocode(
        self,
        latitude: float,
        longitude: float,
    ) -> Dict[str, Any]:
        """
        Convert coordinates to an address.
        
        Args:
            latitude: Latitude
            longitude: Longitude
        
        Returns:
            Dictionary with 'results' containing address information
        """
        url = f"{self.BASE_URL}/geocode/json"
        
        params = {
            "latlng": f"{latitude},{longitude}",
            "key": self.api_key,
        }
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    # ==================== DIRECTIONS API ====================
    
    async def get_directions(
        self,
        origin: str | tuple[float, float],
        destination: str | tuple[float, float],
        mode: str = "driving",
        waypoints: Optional[List[str]] = None,
        alternatives: bool = False,
        avoid: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get directions between two points.
        
        Args:
            origin: Starting point (address string or (lat, lng) tuple)
            destination: End point (address string or (lat, lng) tuple)
            mode: Travel mode (driving, walking, bicycling, transit)
            waypoints: List of intermediate waypoints
            alternatives: Whether to provide alternative routes
            avoid: List of features to avoid (tolls, highways, ferries)
        
        Returns:
            Dictionary with 'routes' containing direction information
        """
        url = f"{self.BASE_URL}/directions/json"
        
        # Convert tuples to string format
        if isinstance(origin, tuple):
            origin = f"{origin[0]},{origin[1]}"
        if isinstance(destination, tuple):
            destination = f"{destination[0]},{destination[1]}"
        
        params = {
            "origin": origin,
            "destination": destination,
            "mode": mode,
            "key": self.api_key,
        }
        
        if waypoints:
            params["waypoints"] = "|".join(waypoints)
        if alternatives:
            params["alternatives"] = "true"
        if avoid:
            params["avoid"] = "|".join(avoid)
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    # ==================== DISTANCE MATRIX API ====================
    
    async def get_distance_matrix(
        self,
        origins: List[str | tuple[float, float]],
        destinations: List[str | tuple[float, float]],
        mode: str = "driving",
        units: str = "metric",
    ) -> Dict[str, Any]:
        """
        Calculate travel distance and time between multiple origins and destinations.
        
        Args:
            origins: List of starting points
            destinations: List of end points
            mode: Travel mode (driving, walking, bicycling, transit)
            units: Distance units (metric or imperial)
        
        Returns:
            Dictionary with distance and duration information
        """
        url = f"{self.BASE_URL}/distancematrix/json"
        
        # Convert tuples to string format
        origin_strs = []
        for origin in origins:
            if isinstance(origin, tuple):
                origin_strs.append(f"{origin[0]},{origin[1]}")
            else:
                origin_strs.append(origin)
        
        dest_strs = []
        for dest in destinations:
            if isinstance(dest, tuple):
                dest_strs.append(f"{dest[0]},{dest[1]}")
            else:
                dest_strs.append(dest)
        
        params = {
            "origins": "|".join(origin_strs),
            "destinations": "|".join(dest_strs),
            "mode": mode,
            "units": units,
            "key": self.api_key,
        }
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    # ==================== HELPER METHODS ====================
    
    async def find_eco_friendly_places(
        self,
        latitude: float,
        longitude: float,
        radius: int = 5000,
    ) -> List[Dict[str, Any]]:
        """
        Find eco-friendly places (parks, nature reserves, bike rentals, etc.)
        
        Args:
            latitude: Center point latitude
            longitude: Center point longitude
            radius: Search radius in meters
        
        Returns:
            List of eco-friendly places with details
        """
        eco_keywords = ["eco", "sustainable", "organic", "green", "bicycle", "bike"]
        eco_types = ["park", "bicycle_store", "transit_station"]
        
        all_results = []
        
        # Search by type
        for place_type in eco_types:
            try:
                result = await self.search_nearby_places(
                    latitude=latitude,
                    longitude=longitude,
                    radius=radius,
                    place_type=place_type,
                )
                if result.get("results"):
                    all_results.extend(result["results"])
            except Exception as e:
                print(f"Error searching for {place_type}: {e}")
        
        # Search by keyword
        for keyword in eco_keywords:
            try:
                result = await self.search_nearby_places(
                    latitude=latitude,
                    longitude=longitude,
                    radius=radius,
                    keyword=keyword,
                )
                if result.get("results"):
                    all_results.extend(result["results"])
            except Exception as e:
                print(f"Error searching for keyword {keyword}: {e}")
        
        # Remove duplicates based on place_id
        unique_places = {}
        for place in all_results:
            place_id = place.get("place_id")
            if place_id and place_id not in unique_places:
                unique_places[place_id] = place
        
        return list(unique_places.values())


# Singleton instance for easy access
_maps_client_instance: Optional[GoogleMapsClient] = None


async def get_maps_client() -> GoogleMapsClient:
    """Get or create a singleton GoogleMapsClient instance."""
    global _maps_client_instance
    if _maps_client_instance is None:
        _maps_client_instance = GoogleMapsClient()
    return _maps_client_instance
