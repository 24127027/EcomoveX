from typing import Any, Dict, List, Optional, Tuple
import httpx
from schemas.route_schema import *
from schemas.map_schema import *
from utils.config import settings
from utils.maps.map_utils import interpolate_search_params
from schemas.destination_schema import Location, Bounds

TRANSPORT_MODE_TO_ROUTES_API = {
    "car": "DRIVE",
    "motorbike": "DRIVE",
    "walking": "WALK",
    "bus": "TRANSIT",
    "metro": "TRANSIT",
    "train": "TRANSIT"
}

class MapAPI:   
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GOOGLE_API_KEY
        if not self.api_key:
            raise ValueError("Google map API key is required")
        
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
                params["location"] = f"{data.user_location.latitude},{data.user_location.longitude}"
            if data.radius:
                params["radius"] = data.radius
            if data.place_types:
                params["types"] = data.place_types
            if components:
                params["components"] = components
            
            url = f"{self.base_url}/place/autocomplete/json"
            response = await self.client.get(url, params=params)
            
            if response.status_code != 200:
                raise ValueError(f"Error in autocomplete: HTTP {response.status_code}")
            
            data = response.json()
            if data.get("status") != "OK":
                raise ValueError(f"Error in autocomplete: {data.get('status')}")            
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
            
            if response.status_code != 200:
                raise ValueError(f"Error fetching place details: HTTP {response.status_code}")
            
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
                    location=Location(
                        latitude=data.get("result", {}).get("geometry", {}).get("location", {}).get("lat"),
                        longitude=data.get("result", {}).get("geometry", {}).get("location", {}).get("lng")
                    ),
                    bounds=Bounds(
                        northeast=Location(
                            latitude=data.get("result", {}).get("geometry", {}).get("viewport", {}).get("northeast", {}).get("lat"),
                            longitude=data.get("result", {}).get("geometry", {}).get("viewport", {}).get("northeast", {}).get("lng")
                        ),
                        southwest=Location(
                            latitude=data.get("result", {}).get("geometry", {}).get("viewport", {}).get("southwest", {}).get("lat"),
                            longitude=data.get("result", {}).get("geometry", {}).get("viewport", {}).get("southwest", {}).get("lng")
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
                    photo_url=await self.generate_place_photo_url(photo.get("photo_reference")),  
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
            
    async def reverse_geocode(
        self,
        location: Location,
        language: str = "vi"
    ) -> GeocodingResponse:
        try:
            params = {
                "latlng": f"{location.latitude},{location.longitude}",
                "language": language,
                "key": self.api_key
            }
            
            url = f"{self.base_url}/geocode/json"
            response = await self.client.get(url, params=params)
            
            if response.status_code != 200:
                raise ValueError(f"Error in reverse geocoding: HTTP {response.status_code}")
            
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
                        location=Location(
                            latitude=result.get("geometry", {}).get("location", {}).get("lat"),
                            longitude=result.get("geometry", {}).get("location", {}).get("lng")
                        ),
                        bounds=Bounds(
                            northeast=Location(
                                latitude=result.get("geometry", {}).get("viewport", {}).get("northeast", {}).get("lat"),
                                longitude=result.get("geometry", {}).get("viewport", {}).get("northeast", {}).get("lng")
                            ),
                            southwest=Location(
                                latitude=result.get("geometry", {}).get("viewport", {}).get("southwest", {}).get("lat"),
                                longitude=result.get("geometry", {}).get("viewport", {}).get("southwest", {}).get("lng")
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
            
            if response.status_code != 200:
                raise ValueError(f"Error in geocoding: HTTP {response.status_code}")
            
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
                        location=Location(
                            latitude=result.get("geometry", {}).get("location", {}).get("lat"),
                            longitude=result.get("geometry", {}).get("location", {}).get("lng")
                        ),
                        bounds=Bounds(
                            northeast=Location(
                                latitude=result.get("geometry", {}).get("viewport", {}).get("northeast", {}).get("lat"),
                                longitude=result.get("geometry", {}).get("viewport", {}).get("northeast", {}).get("lng")
                            ),
                            southwest=Location(
                                latitude=result.get("geometry", {}).get("viewport", {}).get("southwest", {}).get("lat"),
                                longitude=result.get("geometry", {}).get("viewport", {}).get("southwest", {}).get("lng")
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
        data: NearbyPlaceRequest,
        language: str = "vi"
    ) -> NearbyPlacesResponse:
        try:
            params = {
                "location": f"{data.location.latitude},{data.location.longitude}",
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
            
            if response.status_code != 200:
                raise ValueError(f"Error fetching nearby places: HTTP {response.status_code}")
            
            response_data = response.json()
            if response_data.get("status") != "OK":
                raise ValueError(f"Error fetching nearby places: {response_data.get('status')}")
            
            places = [
                NearbyPlaceSimple(
                    place_id=result["place_id"],
                    name=result["name"],
                    location=Location(
                        latitude=result["geometry"]["location"]["lat"], 
                        longitude=result["geometry"]["location"]["lng"]
                    ),
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
        
    async def get_next_page_nearby_places(
        self,
        page_token: str,
    ) -> NearbyPlacesResponse:
        try:
            params = {
                "pagetoken": page_token,
                "key": self.api_key
            }
            url = f"{self.base_url}/place/nearbysearch/json"
            response = await self.client.get(url, params=params)
            
            if response.status_code != 200:
                raise ValueError(f"Error fetching next page of nearby places: HTTP {response.status_code}")
            
            response_data = response.json()
            if response_data.get("status") != "OK":
                raise ValueError(f"Error fetching next page of nearby places: {response_data.get('status')}")            
            places = [
                NearbyPlaceSimple(
                    place_id=result["place_id"],
                    name=result["name"],
                    location=Location(
                        latitude=result["geometry"]["location"]["lat"],
                        longitude=result["geometry"]["location"]["lng"]
                    ),
                    rating=result.get("rating"),
                    types=result.get("types", []),
                )
                for result in response_data.get("results", [])
            ]
            
            return NearbyPlacesResponse(
                center=None,
                places=places,
                next_page_token=response_data.get("next_page_token")
            )
        except Exception as e:
            print(f"Error in get_next_page_nearby_places: {e}")
            raise e
        
    async def search_along_route(
        self,
        directions: DirectionsResponse,
        search_type: str,
    ) -> SearchAlongRouteResponse:
        try:
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
                    NearbyPlaceRequest(
                        location=point,
                        radius=interpolate[0],
                        place_type=search_type
                    )
                )
                for place in data.places:
                    if place.place_id not in seen_place_ids:
                        seen_place_ids.add(place.place_id)
                        all_places.append(place)
            
            return SearchAlongRouteResponse(
                places_along_route=all_places,
            )
        except Exception as e:
            print(f"Error in search_along_route: {e}")
            raise e
    
    async def generate_place_photo_url(
        self,
        photo_reference: str,
        maxwidth: int = 400,
    ) -> str:
        try:
            params = {
                "maxwidth": maxwidth,
                "photoreference": photo_reference,
                "key": self.api_key
            }

            base_url = "https://maps.googleapis.com/maps/api/place/photo"
            response = await self.client.get(base_url, params=params, follow_redirects=False)
            
            if response.status_code != 302:
                raise ValueError(f"Error fetching photo URL: HTTP {response.status_code}")
            
            real_photo_url = response.headers.get("Location")

            return real_photo_url

        except Exception as e:
            print(f"Error in generate_place_photo_url: {e}")
            raise e

async def create_map_client(api_key: Optional[str] = None) -> MapAPI:
    return MapAPI(api_key=api_key)