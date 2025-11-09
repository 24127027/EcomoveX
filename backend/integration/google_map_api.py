import math
from typing import Any, Dict, List, Optional, Tuple
import httpx
from models.route import TransportMode
from schemas.map_schema import *
from utils.config import settings

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
        extra_computations: Optional[List[str]] = None,
        language_code: str = "vi"
    ) -> Dict[str, Any]:
        """Get current air quality data with optional pollutant details"""
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
    
    # ============= CORE FEATURES FOR ECO APP =============
    
    async def get_directions_with_traffic(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        mode: TransportMode,
        departure_time: Optional[str] = "now",
        language: str = "vi"
    ) -> RouteWithTrafficResponse:
        """Get route with real-time traffic information"""
        params = {
            "origin": f"{origin[0]},{origin[1]}",
            "destination": f"{destination[0]},{destination[1]}",
            "mode": mode.value,
            "departure_time": departure_time,
            "language": language,
            "key": self.api_key
        }
        
        url = f"{self.base_url}/directions/json"
        response = await self.client.get(url, params=params)
        data = response.json()
        
        if data.get("status") != "OK" or not data.get("routes"):
            return RouteWithTrafficResponse(
                status=data.get("status", "ERROR"),
                error_message=data.get("error_message", "No routes found")
            )
        
        route_data = data["routes"][0]
        leg = route_data["legs"][0]
        
        route = Route(**route_data)
        
        traffic_info = None
        if leg.get("duration_in_traffic"):
            normal_duration = leg["duration"]["value"]
            traffic_duration = leg["duration_in_traffic"]["value"]
            delay = traffic_duration - normal_duration
            
            if delay < 300:
                level = "light"
            elif delay < 900:
                level = "moderate"
            elif delay < 1800:
                level = "heavy"
            else:
                level = "severe"
            
            traffic_info = TrafficCondition(
                duration_in_traffic=traffic_duration,
                duration_normal=normal_duration,
                traffic_level=level,
            )
        
        return RouteWithTrafficResponse(
            status="OK",
            route=route,
            traffic=traffic_info
        )
        
    async def get_eco_optimized_routes(
        self,
        request: EcoRouteRequest,
        carbon_service=None
    ) -> EcoRouteResponse:
        """Get eco-friendly route recommendations optimized for lowest carbon footprint"""
        all_routes = []
        
        # Try different eco-friendly modes
        for mode_str in request.preferred_modes:
            try:
                mode = TransportMode[mode_str]
            except KeyError:
                continue
            
            params = {
                "origin": f"{request.origin[0]},{request.origin[1]}",
                "destination": f"{request.destination[0]},{request.destination[1]}",
                "mode": mode.value,
                "language": "vi",
                "key": self.api_key
            }
            
            if request.avoid_highways:
                params["avoid"] = "highways"
            if request.departure_time:
                params["departure_time"] = request.departure_time
            
            url = f"{self.base_url}/directions/json"
            response = await self.client.get(url, params=params)
            data = response.json()
            
            if data.get("status") == "OK" and data.get("routes"):
                route = data["routes"][0]
                leg = route["legs"][0]
                distance_km = leg["distance"]["value"] / 1000
                duration_min = leg["duration"]["value"] / 60
                
                # Skip if exceeds max duration
                if request.max_duration_minutes and duration_min > request.max_duration_minutes:
                    continue
                
                # Calculate carbon (mock if service not available)
                carbon_kg = distance_km * 0.02  # Placeholder
                
                # Calculate eco score (0-100)
                eco_score = 100
                if mode_str == "walking":
                    eco_score = 100
                elif mode_str == "cycling":
                    eco_score = 95
                elif mode_str == "transit":
                    eco_score = 85
                elif mode_str == "bus":
                    eco_score = 80
                
                all_routes.append(EcoRouteData(
                    mode=[mode_str],
                    distance_km=distance_km,
                    duration_minutes=duration_min,
                    carbon_kg=carbon_kg,
                    carbon_saved_vs_car=max(0, distance_km * 0.12 - carbon_kg),
                    eco_score=eco_score,
                    polyline=route["overview_polyline"]["points"],
                    bounds=Bounds(
                        northeast=tuple(route["bounds"]["northeast"].values()),
                        southwest=tuple(route["bounds"]["southwest"].values())
                    )
                ))
        
        if not all_routes:
            return EcoRouteResponse(
                status="ZERO_RESULTS",
                comparison_with_car=None
            )
        
        # Sort by eco score
        all_routes.sort(key=lambda x: (-x.eco_score, x.duration_minutes))
        
        return EcoRouteResponse(
            status="OK",
            recommended_route=all_routes[0],
            alternatives=all_routes[1:3],
            comparison_with_car={
                "carbon_saved_kg": all_routes[0].carbon_saved_vs_car,
                "trees_equivalent": round(all_routes[0].carbon_saved_vs_car / 0.02, 1)
            }
        )
    
    async def search_ev_charging_stations(
        self,
        lat: float,
        lng: float,
        radius: int = 5000,
        language: str = "vi"
    ) -> NearbyPlacesResponse:
        """Search for EV charging stations nearby"""
        params = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "keyword": "ev charging station|electric vehicle charging",
            "language": language,
            "key": self.api_key
        }
        
        url = f"{self.base_url}/place/nearbysearch/json"
        response = await self.client.get(url, params=params)
        data = response.json()
        
        if data.get("status") not in ["OK", "ZERO_RESULTS"]:
            return NearbyPlacesResponse(
                status=data.get("status", "ERROR"),
                center=(lat, lng),
                places=[]
            )
        
        places = [
            NearbyPlaceSimple(
                place_id=result["place_id"],
                name=result["name"],
                location=(result["geometry"]["location"]["lat"], 
                         result["geometry"]["location"]["lng"]),
                rating=result.get("rating"),
                types=result.get("types", []),
                vicinity=result.get("vicinity")
            )
            for result in data.get("results", [])[:20]
        ]
        
        return NearbyPlacesResponse(
            status="OK",
            center=(lat, lng),
            places=places,
            next_page_token=data.get("next_page_token")
        )
    
    async def search_bike_sharing_stations(
        self,
        lat: float,
        lng: float,
        radius: int = 2000,
        language: str = "vi"
    ) -> NearbyPlacesResponse:
        """Search for bike sharing stations nearby"""
        params = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "keyword": "bike sharing|bicycle rental|bike station",
            "language": language,
            "key": self.api_key
        }
        
        url = f"{self.base_url}/place/nearbysearch/json"
        response = await self.client.get(url, params=params)
        data = response.json()
        
        if data.get("status") not in ["OK", "ZERO_RESULTS"]:
            return NearbyPlacesResponse(
                status=data.get("status", "ERROR"),
                center=(lat, lng),
                places=[]
            )
        
        places = [
            NearbyPlaceSimple(
                place_id=result["place_id"],
                name=result["name"],
                location=(result["geometry"]["location"]["lat"], 
                         result["geometry"]["location"]["lng"]),
                rating=result.get("rating"),
                types=result.get("types", []),
                vicinity=result.get("vicinity")
            )
            for result in data.get("results", [])[:20]
        ]
        
        return NearbyPlacesResponse(
            status="OK",
            center=(lat, lng),
            places=places,
            next_page_token=data.get("next_page_token")
        )
    
    # ============= UI HELPER FUNCTIONS =============
    
    async def get_air_quality_heatmap(
        self,
        lat: float,
        lng: float,
        zoom: int = 12
    ) -> Dict[str, Any]:
        """Get air quality heatmap tile for UI visualization"""
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
    
    async def get_photo_url(
        self,
        photo_reference: str,
        max_width: int = 400,
        max_height: Optional[int] = None
    ) -> str:
        """Get photo URL for displaying place images in UI"""
        params = {
            "photoreference": photo_reference,
            "maxwidth": max_width,
            "key": self.api_key
        }
        
        if max_height:
            params["maxheight"] = max_height
        
        return f"{self.base_url}/place/photo?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
    
    async def get_multiple_routes_for_comparison(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        modes: List[TransportMode]
    ) -> RouteComparisonResponse:
        """Get routes for multiple transport modes for UI comparison with carbon data"""
        results = {}
        
        for mode in modes:
            try:
                directions = await self.get_directions(
                    origin=origin,
                    destination=destination,
                    mode=mode,
                    alternatives=False
                )
                
                if directions.status == "OK" and directions.routes:
                    route = directions.routes[0]
                    leg = route.legs[0]
                    distance_km = leg.distance.value / 1000
                    
                    # Estimate carbon (simplified)
                    carbon_factors = {
                        "car": 0.12,
                        "motorbike": 0.08,
                        "bus": 0.04,
                        "metro": 0.03,
                        "train": 0.03,
                        "cycling": 0.0,
                        "walking": 0.0
                    }
                    carbon_kg = distance_km * carbon_factors.get(mode.value, 0.1)
                    
                    results[mode.value] = RouteComparisonMode(
                        mode=mode.value,
                        available=True,
                        distance_meters=leg.distance.value,
                        distance_text=leg.distance.text,
                        duration_seconds=leg.duration.value,
                        duration_text=leg.duration.text,
                        carbon_kg=carbon_kg,
                        polyline=route.overview_polyline.points,
                        summary=route.summary,
                        bounds=route.bounds
                    )
                else:
                    results[mode.value] = RouteComparisonMode(
                        mode=mode.value,
                        available=False,
                        error="Route not available for this mode"
                    )
            except Exception as e:
                results[mode.value] = RouteComparisonMode(
                    mode=mode.value,
                    available=False,
                    error=str(e)
                )
        
        return RouteComparisonResponse(
            status="OK",
            origin=origin,
            destination=destination,
            routes=results
        )
    
    async def get_nearby_places_for_map(
        self,
        lat: float,
        lng: float,
        radius: int = 1000,
        place_type: Optional[str] = None,
        keyword: Optional[str] = None,
        language: str = "vi"
    ) -> NearbyPlacesResponse:
        """Get nearby places for displaying on map UI"""
        params = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "language": language,
            "key": self.api_key
        }
        
        if place_type:
            params["type"] = place_type
        if keyword:
            params["keyword"] = keyword
        
        url = f"{self.base_url}/place/nearbysearch/json"
        response = await self.client.get(url, params=params)
        data = response.json()
        
        if data.get("status") not in ["OK", "ZERO_RESULTS"]:
            return NearbyPlacesResponse(
                status=data.get("status", "ERROR"),
                center=(lat, lng),
                places=[]
            )
        
        places = [
            NearbyPlaceSimple(
                place_id=result["place_id"],
                name=result["name"],
                location=(result["geometry"]["location"]["lat"], 
                         result["geometry"]["location"]["lng"]),
                rating=result.get("rating"),
                types=result.get("types", []),
                vicinity=result.get("vicinity")
            )
            for result in data.get("results", [])[:10]
        ]
        
        return NearbyPlacesResponse(
            status="OK",
            center=(lat, lng),
            places=places,
            next_page_token=data.get("next_page_token")
        )
        
    async def search_along_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        search_type: str,
        mode: TransportMode = TransportMode.car
    ) -> SearchAlongRouteResponse:
        """Search for places (gas stations, restaurants, etc.) along a route"""
        # Get the route first
        directions = await self.get_directions(origin, destination, mode)
        
        if directions.status != "OK" or not directions.routes:
            return SearchAlongRouteResponse(
                status="ERROR",
                route_polyline="",
                places_along_route=[],
                search_type=search_type,
                error_message="Could not find route"
            )
        
        route = directions.routes[0]
        
        # Sample points along the route (every ~5km)
        sample_points = []
        total_distance = 0
        sample_interval = 5000  # 5km
        
        for leg in route.legs:
            for step in leg.steps:
                total_distance += step.distance.value
                if total_distance >= sample_interval:
                    sample_points.append(step.start_location)
                    total_distance = 0
        
        # Search for places near each sample point
        all_places = []
        seen_place_ids = set()
        
        for point in sample_points[:5]:  # Limit to 5 sample points
            params = {
                "location": f"{point[0]},{point[1]}",
                "radius": 2000,
                "type": search_type,
                "key": self.api_key
            }
            
            url = f"{self.base_url}/place/nearbysearch/json"
            response = await self.client.get(url, params=params)
            data = response.json()
            
            if data.get("status") == "OK":
                for place in data.get("results", [])[:3]:  # Top 3 per point
                    place_id = place.get("place_id")
                    if place_id not in seen_place_ids:
                        seen_place_ids.add(place_id)
                        location = place.get("geometry", {}).get("location", {})
                        all_places.append(PlaceDetailsResponse(
                            place_id=place_id,
                            name=place.get("name"),
                            location=(location.get("lat"), location.get("lng")),
                            rating=place.get("rating"),
                            vicinity=place.get("vicinity"),
                            types=place.get("types", [])
                        ))
        
        return SearchAlongRouteResponse(
            status="OK",
            route_polyline=route.overview_polyline.points,
            places_along_route=all_places[:10],
            search_type=search_type
        )


async def create_maps_client(api_key: Optional[str] = None) -> GoogleMapsAPI:
    return GoogleMapsAPI(api_key=api_key)