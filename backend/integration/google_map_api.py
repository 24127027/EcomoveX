import math
from typing import Any, Dict, List, Optional, Tuple
import httpx
from models.route import TransportMode
from schemas.map_schema import *
from utils.config import settings
from utils.maps.map_utils import interpolate_search_params

# Mapping Google Maps API travel modes to our TransportMode enum
GOOGLE_TO_TRANSPORT_MODE = {
    "driving": TransportMode.car,
    "walking": TransportMode.walking,
    "bicycling": TransportMode.motorbike,  # Best approximation
    "transit": TransportMode.bus,  # Can be bus, train, or metro
}

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
        try:
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
            data = response.json()
            if data.get("status") != "OK":
                raise ValueError(f"Error fetching autocomplete places: {data.get('status')}")
            list = data.get("predictions", [])
            list_places = []
            for place in list:
                place_obj = PlaceSearchDisplay(
                    description=place.get("description"),
                    place_id=place.get("place_id"),
                    structured_formatting=place.get("structured_formatting"),
                    types=place.get("types", []),
                    matched_substrings=place.get("matched_substrings", []),
                    distance=place.get("distance")
                )
                list_places.append(place_obj)
            return AutocompleteResponse(predictions=list_places)
        except Exception as e:
            print(f"Error in autocomplete_place: {e}")
            raise e

    async def get_place_details_from_autocomplete(self, place_id: str, language: str = "vi") -> PlaceDetailsResponse:
        try:
            fields = [
                "place_id",
                "name", 
                "formatted_address",
                "address_components",
                "formatted_phone_number",
                "geometry/location",
                "geometry/viewport",
                "types",
                "rating",
                "user_ratings_total",
                "price_level",
                "opening_hours",
                "website",
                "photos",
                "reviews",
                "vicinity",
                "utc_offset",
            ]
            params = {
                "place_id": place_id,
                "fields": ",".join(fields),
                "language": language,
                "key": self.api_key
            }
            
            url = f"{self.base_url}/place/details/json"
            response = await self.client.get(url, params=params)
            data = response.json()
            if data.get("status") != "OK":
                raise ValueError(f"Error fetching place details: {data.get('status')}")
            return PlaceDetailsResponse(
                place_id=data.get("result", {}).get("place_id"),
                name=data.get("result", {}).get("name"),
                formatted_address=data.get("result", {}).get("formatted_address"),
                address_components=[AddressComponent(
                    name=comp.get("long_name"),
                    types=comp.get("types", [])
                ) for comp in data.get("result", {}).get("address_components", [])],
                formatted_phone_number=data.get("result", {}).get("formatted_phone_number"),
                geometry=Geometry(
                    location=(
                        data.get("result", {}).get("geometry", {}).get("location", {}).get("lat"),
                        data.get("result", {}).get("geometry", {}).get("location", {}).get("lng")
                    ),
                    bounds=Bounds(
                        northeast=(
                            data.get("result", {}).get("geometry", {}).get("viewport", {}).get("northeast", {}).get("lat"),
                            data.get("result", {}).get("geometry", {}).get("viewport", {}).get("northeast", {}).get("lng")
                        ),
                        southwest=(
                            data.get("result", {}).get("geometry", {}).get("viewport", {}).get("southwest", {}).get("lat"),
                            data.get("result", {}).get("geometry", {}).get("viewport", {}).get("southwest", {}).get("lng")
                        )
                    ),
                ),
                types=data.get("result", {}).get("types", []),
                rating=data.get("result", {}).get("rating"),
                user_ratings_total=data.get("result", {}).get("user_ratings_total"),
                price_level=data.get("result", {}).get("price_level"),
                opening_hours=OpeningHours(
                    open_now=data.get("result", {}).get("opening_hours", {}).get("open_now", False),
                    periods=data.get("result", {}).get("opening_hours", {}).get("periods"),
                    weekday_text=data.get("result", {}).get("opening_hours", {}).get("weekday_text")
                ) if data.get("result", {}).get("opening_hours") else None,
                website=data.get("result", {}).get("website"),
                photos=[PhotoInfo(
                    photo_reference=photo.get("photo_reference"),  
                    size=(photo.get("width"), photo.get("height"))
                ) for photo in data.get("result", {}).get("photos", [])] if data.get("result", {}).get("photos") else None,
                reviews=[Review(
                    rating=review.get("rating"),
                    text=review.get("text")
                ) for review in data.get("result", {}).get("reviews", [])] if data.get("result", {}).get("reviews") else None,
                utc_offset=data.get("result", {}).get("utc_offset"),
            )
        except Exception as e:
            print(f"Error in get_place_details_from_autocomplete: {e}")
            raise e
    
    async def get_directions(
        self,
        data: DirectionsRequest,
        mode: TransportMode,
        language: str = "vi"
    ) -> DirectionsResponse:
        try:
            params = {
                "origin": f"{data.origin[0]},{data.origin[1]}",
                "destination": f"{data.destination[0]},{data.destination[1]}",
                "mode": mode.value,
                "departure_time": "now" if data.get_traffic else None,
                "alternatives": str(data.alternatives).lower(),
                "language": language,
                "key": self.api_key
            }
            
            if data.waypoints:
                waypoints_str = "|".join([f"{wp[0]},{wp[1]}" for wp in data.waypoints])
                params["waypoints"] = "optimize:true|" + waypoints_str
            if data.avoid:
                params["avoid"] = "|".join(data.avoid)
            
            url = f"{self.base_url}/directions/json"
            response = await self.client.get(url, params=params)
            response_data = response.json()
            if response_data.get("status") != "OK":
                raise ValueError(f"Error fetching directions: {response_data.get('status')}")

            routes = []
            for route_data in response_data.get("routes", []):
                legs = []
                for leg_data in route_data.get("legs", []):
                    steps = []
                    for step_data in leg_data.get("steps", []):
                        # Map Google's travel mode to our TransportMode enum
                        google_mode = step_data["travel_mode"].lower()
                        transport_mode = GOOGLE_TO_TRANSPORT_MODE.get(google_mode, TransportMode.walking)
                        
                        steps.append(
                            Step(
                                distance=step_data["distance"]["value"],
                                duration=step_data["duration"]["value"],
                                start_location=(step_data["start_location"]["lat"], step_data["start_location"]["lng"]),
                                end_location=(step_data["end_location"]["lat"], step_data["end_location"]["lng"]),
                                html_instructions=step_data.get("html_instructions", ""),
                                travel_mode=transport_mode,
                                polyline=step_data.get("polyline", {}).get("points"),
                                transit_details=step_data.get("transit_details")
                            )
                        )
                    leg = Leg(
                        distance=leg_data["distance"]["value"],
                        duration=leg_data["duration"]["value"],
                        start_location=(leg_data["start_address"], (leg_data["start_location"]["lat"], leg_data["start_location"]["lng"])),
                        end_location=(leg_data["end_address"], (leg_data["end_location"]["lat"], leg_data["end_location"]["lng"])),
                        steps=steps,
                        duration_in_traffic=leg_data.get("duration_in_traffic", {}).get("value"),
                        arrival_time=leg_data.get("arrival_time"),
                        departure_time=leg_data.get("departure_time")
                    )
                    legs.append(leg)
                route = Route(
                    summary=route_data.get("summary", ""),
                    legs=legs,
                    overview_polyline=route_data.get("overview_polyline", {}).get("points", ""),
                    bounds=Bounds(
                        northeast=(route_data["bounds"]["northeast"]["lat"], route_data["bounds"]["northeast"]["lng"]),
                        southwest=(route_data["bounds"]["southwest"]["lat"], route_data["bounds"]["southwest"]["lng"])
                    ),
                    distance=sum(leg.distance for leg in legs),
                    duration=sum(leg.duration for leg in legs),
                    duration_in_traffic=route_data.get("duration_in_traffic", {}).get("value") if "duration_in_traffic" in route_data else None
                )
                routes.append(route)
            return DirectionsResponse(routes=routes, available_travel_modes=mode)
        except Exception as e:
            print(f"Error in get_directions: {e}")
            raise e
    
    async def get_direction_for_multiple_modes(
        self,
        data: DirectionsRequest,
        modes: List[TransportMode]
    ) -> List[DirectionsResponse]:
        try:
            all_responses = []
            
            for mode in modes:
                directions = await self.get_directions(
                    data=data,
                    mode=mode
                )
                all_responses.append(directions)
            
            return all_responses    
        except Exception as e:
            print(f"Error in get_direction_for_multiple_modes: {e}")
            raise e
    
    async def get_air_quality(
        self,
        location: Tuple[float, float],
        extra_computations: Optional[List[str]] = ["HEALTH_RECOMMENDATIONS"],
        language_code: str = "vi"
    ) -> AirQualityResponse:
        try:
            payload = {
                "location": {
                    "latitude": location[0],
                    "longitude": location[1]
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
            data=response.json()
            if data.get("status") != "OK":
                raise ValueError(f"Error fetching air quality data: {data.get('status')}")
            return AirQualityResponse(
                location=location,
                aqi_data=AirQualityIndex(
                    display_name="Universal Air Quality Index",
                    aqi=data.get("indexes", {}).get("aqi"),
                    category=data.get("indexes", {}).get("category")
                ),
                recommendations=HealthRecommendation(
                    general_population=data.get("healthRecommendations", {}).get("generalPopulation"),
                    sensitive_groups=data.get("healthRecommendations", {}).get("sensitiveGroups")
                    )
            )
        except Exception as e:
            print(f"Error in get_air_quality: {e}")
            raise e
    
    async def reverse_geocode(
        self,
        location: Tuple[float, float],
        language: str = "vi"
    ) -> GeocodingResponse:
        try:
            params = {
                "latlng": f"{location[0]},{location[1]}",
                "language": language,
                "key": self.api_key
            }
            
            url = f"{self.base_url}/geocode/json"
            response = await self.client.get(url, params=params)
            data = response.json()
            if data.get("status") != "OK":
                raise ValueError(f"Error in reverse geocoding: {data.get('status')}")
            
            results = []
            for result in data.get("results", []):
                results.append(GeocodingResult(
                    place_id=result.get("place_id"),
                    formatted_address=result.get("formatted_address"),
                    address_components=[AddressComponent(
                        name=comp.get("long_name"),
                        types=comp.get("types", [])
                    ) for comp in result.get("address_components", [])],
                    geometry=Geometry(
                        location=(
                            result.get("geometry", {}).get("location", {}).get("lat"),
                            result.get("geometry", {}).get("location", {}).get("lng")
                        ),
                        bounds=Bounds(
                            northeast=(
                                result.get("geometry", {}).get("viewport", {}).get("northeast", {}).get("lat"),
                                result.get("geometry", {}).get("viewport", {}).get("northeast", {}).get("lng")
                            ),
                            southwest=(
                                result.get("geometry", {}).get("viewport", {}).get("southwest", {}).get("lat"),
                                result.get("geometry", {}).get("viewport", {}).get("southwest", {}).get("lng")
                            )
                        )
                    ),
                    types=result.get("types", [])
                ))
            
            return GeocodingResponse(results=results)
        except Exception as e:
            print(f"Error in reverse_geocode: {e}")
            raise e
    
    async def geocode(
        self,
        address: str,
        language: str = "vi",
        region: str = "vn"
    ) -> GeocodingResponse:
        try:
            params = {
                "address": address,
                "language": language,
                "region": region,
                "key": self.api_key
            }
            
            url = f"{self.base_url}/geocode/json"
            response = await self.client.get(url, params=params)
            data = response.json()
            if data.get("status") != "OK":
                raise ValueError(f"Error in geocoding: {data.get('status')}")
            
            results = []
            for result in data.get("results", []):
                results.append(GeocodingResult(
                    place_id=result.get("place_id"),
                    formatted_address=result.get("formatted_address"),
                    address_components=[AddressComponent(
                        name=comp.get("long_name"),
                        types=comp.get("types", [])
                    ) for comp in result.get("address_components", [])],
                    geometry=Geometry(
                        location=(
                            result.get("geometry", {}).get("location", {}).get("lat"),
                            result.get("geometry", {}).get("location", {}).get("lng")
                        ),
                        bounds=Bounds(
                            northeast=(
                                result.get("geometry", {}).get("viewport", {}).get("northeast", {}).get("lat"),
                                result.get("geometry", {}).get("viewport", {}).get("northeast", {}).get("lng")
                            ),
                            southwest=(
                                result.get("geometry", {}).get("viewport", {}).get("southwest", {}).get("lat"),
                                result.get("geometry", {}).get("viewport", {}).get("southwest", {}).get("lng")
                            )
                        )
                    ),
                    types=result.get("types", [])
                ))
            
            return GeocodingResponse(results=results)
        except Exception as e:
            print(f"Error in geocode: {e}")
            raise e
        
    async def get_nearby_places_for_map(
        self,
        data: NearbyPlaceResquest,
        page_token: Optional[str] = None,   
        language: str = "vi"
    ) -> NearbyPlacesResponse:
        try:
            if page_token:
                params = {
                    "pagetoken": page_token,
                    "key": self.api_key
                }
            else:
                params = {
                    "location": f"{data.location[0]},{data.location[1]}",
                    "radius": data.radius if data.radius else 3600,
                    "rankby": data.rank_by,
                    "language": language,
                    "key": self.api_key
                }
                if data.place_type:
                    params["type"] = data.place_type
                if data.keyword:
                    params["keyword"] = data.keyword
            
            url = f"{self.base_url}/place/nearbysearch/json"
            response = await self.client.get(url, params=params)
            response_data = response.json()
            
            if response_data.get("status") != "OK":
                raise ValueError(f"Error fetching nearby places: {response_data.get('status')}")
            
            places = [
                NearbyPlaceSimple(
                    place_id=result["place_id"],
                    name=result["name"],
                    location=(result["geometry"]["location"]["lat"], 
                            result["geometry"]["location"]["lng"]),
                    rating=result.get("rating"),
                    types=result.get("types", []),
                )
                for result in response_data.get("results", [])
            ]
            
            return NearbyPlacesResponse(
                center=data.location,
                places=places,
                next_page_token=response_data.get("next_page_token")
            )
        except Exception as e:
            print(f"Error in get_nearby_places_for_map: {e}")
            raise e
  
    async def search_along_route(
        self,
        data: DirectionsRequest,
        travel_mode: TransportMode,
        search_type: str,
    ) -> SearchAlongRouteResponse:
        directions = await self.get_directions(data=data, mode=travel_mode)        
        route = directions.routes[0]
        
        sample_points = []
        total_distance = 0
        interpolate = await interpolate_search_params(distance=route.legs[0].distance)
        sample_interval = interpolate[1]
        
        for leg in route.legs:
            for step in leg.steps:
                total_distance += step.distance
                if total_distance >= sample_interval:
                    sample_points.append(step.start_location)
                    total_distance = 0
        
        all_places = []
        seen_place_ids = set()
        
        for point in sample_points:
            data = await self.get_nearby_places_for_map(
                NearbyPlaceResquest(
                    location=point,
                    radius=interpolate[0],
                    place_type=search_type
                )
            )
            for place in data.places:  # Top 3 per point
                if place.place_id not in seen_place_ids:
                    seen_place_ids.add(place.place_id)
                    all_places.append(NearbyPlaceSimple(
                        place_id=place.place_id,
                        name=place.name,
                        location=place.location,
                        rating=place.rating,
                        types=place.types
                    ))
        
        return SearchAlongRouteResponse(
            route_polyline=route.overview_polyline,
            places_along_route=all_places,
            search_type=search_type
        )


async def create_maps_client(api_key: Optional[str] = None) -> GoogleMapsAPI:
    return GoogleMapsAPI(api_key=api_key)