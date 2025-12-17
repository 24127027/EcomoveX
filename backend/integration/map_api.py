from typing import Optional

import asyncio
import httpx

from schemas.destination_schema import Bounds, Location
from schemas.map_schema import (
    AddressComponent,
    AutocompleteRequest,
    AutocompleteResponse,
    GeocodingResponse,
    GeocodingResult,
    Geometry,
    NearbyPlaceRequest,
    NearbyPlaceSimple,
    NearbyPlacesResponse,
    OpeningHours,
    PhotoInfo,
    PlaceDetailsResponse,
    PlaceSearchDisplay,
    Review,
    SearchAlongRouteResponse,
    TextSearchRequest,
    TextSearchResponse,
)
from schemas.route_schema import DirectionsResponse
from utils.config import settings
from utils.maps.map_utils import interpolate_search_params

TRANSPORT_MODE_TO_ROUTES_API = {
    "car": "DRIVE",
    "motorbike": "DRIVE",
    "walking": "WALK",
    "bus": "TRANSIT",
    "metro": "TRANSIT",
    "train": "TRANSIT",
}


class MapAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GOOGLE_API_KEY
        if not self.api_key:
            raise ValueError("Google map API key is required")

        self.base_url = "https://maps.googleapis.com/maps/api"
        self.new_base_url = "https://places.googleapis.com/v1/places/"
        
        # Create client with better timeout and connection settings
        # Increase timeout and add retries for flaky connections
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            verify=True,  # Ensure SSL verification is enabled
        )

    async def text_search_place(self, request: TextSearchRequest, convert_photo_urls: bool = False) -> TextSearchResponse:
        url = f"{self.new_base_url}:searchText"

        default_mask = (
            "places.id,"
            "places.displayName,places.formattedAddress,places.photos,places.types,places.location"
        )

        selected_mask = request.field_mask if request.field_mask else default_mask

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": selected_mask,
        }

        body = {"textQuery": request.query}
        if request.location and request.radius:
            body["locationBias"] = {
                "circle": {
                    "center": {
                        "latitude": request.location.latitude,
                        "longitude": request.location.longitude,
                    },
                    "radius": request.radius,
                }
            }

        if request.place_types:
            body["includedType"] = request.place_types

        # Retry logic for transient network errors
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                response = await self.client.post(url, headers=headers, json=body)
                response.raise_for_status()

                data = response.json()

                if "places" in data:
                    for place in data["places"]:
                        raw_photos = place.get("photos", [])

                        if (
                            raw_photos
                            and isinstance(raw_photos, list)
                            and len(raw_photos) > 0
                        ):
                            first_photo = raw_photos[0]

                            ref = first_photo.get("name")
                            width = first_photo.get("widthPx", 0)
                            height = first_photo.get("heightPx", 0)

                            photo_info = {
                                "photo_reference": ref,
                                "size": (width, height),
                            }

                            # Only convert to URL if requested
                            if convert_photo_urls and ref:
                                final_url = await self.generate_place_photo_url(ref)
                                photo_info["photo_url"] = final_url
                            else:
                                photo_info["photo_url"] = None

                            place["photos"] = photo_info
                        else:
                            place["photos"] = None

                return TextSearchResponse(**data)
                
            except httpx.ConnectError as e:
                if attempt < max_retries:
                    print(f"Network connection error (attempt {attempt + 1}/{max_retries + 1}): {str(e)}")
                    await asyncio.sleep(0.5)  # Brief delay before retry
                    continue
                print(f"Network connection error in text_search_place after {max_retries + 1} attempts: {str(e)}")
                print(f"URL: {url}")
                raise ValueError(f"Network connection error: Unable to reach Google Places API after {max_retries + 1} attempts. Check your internet connection.")
            except httpx.TimeoutException as e:
                if attempt < max_retries:
                    print(f"Timeout error (attempt {attempt + 1}/{max_retries + 1}): {str(e)}")
                    await asyncio.sleep(0.5)
                    continue
                print(f"Timeout error in text_search_place: {str(e)}")
                raise ValueError(f"Request timeout: Google Places API took too long to respond.")
            except httpx.HTTPStatusError as e:
                print(f"Google Places API Error: {e.response.text}")
                raise ValueError(f"Google Places API returned error {e.response.status_code}: {e.response.text}")
            except Exception as e:
                print(f"Unexpected error in text_search_place: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
                raise e

    async def close(self):
        await self.client.aclose()

    async def autocomplete_place(
        self, data: AutocompleteRequest, components: str = "country:vn"
    ) -> AutocompleteResponse:
        try:
            params = {
                "input": data.query.strip(),
                "language": data.language,
                "key": self.api_key,
                "limit": 3,
                "sessiontoken": data.session_token,
            }

            if data.user_location:
                params["location"] = (
                    f"{data.user_location.latitude},{data.user_location.longitude}"
                )
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
                if data.get("status") == "ZERO_RESULTS":
                    return AutocompleteResponse(predictions=[])
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
                    distance=place.get("distance"),
                )
                list_places.append(place_obj)
            return AutocompleteResponse(predictions=list_places)
        except Exception as e:
            print(f"Error in autocomplete_place: {e}")
            raise e

    async def get_place_details(
        self,
        place_id: str,
        fields: list[str],
        session_token: Optional[str] = None,
        language: str = "vi",
    ) -> PlaceDetailsResponse:
        try:
            params = {
                "place_id": place_id,
                "fields": ",".join(fields),
                "language": language,
                "key": self.api_key,
            }

            if session_token:
                params["sessiontoken"] = session_token

            url = f"{self.base_url}/place/details/json"
            response = await self.client.get(url, params=params)

            if response.status_code != 200:
                raise ValueError(
                    f"Error fetching place details: HTTP {response.status_code}"
                )

            data = response.json()
            if data.get("status") != "OK":
                print(f"API Error Status: {data.get('status')}, Full response: {data}")
                raise ValueError(f"Error fetching place details: {data.get('status')}")
            result = data.get("result", {})
            
            if not result.get("place_id"):
                print(f"WARNING: place_id is None in response for place_id={place_id}")
                print(f"Full result: {result}")
                print(f"API Status: {data.get('status')}")

            return PlaceDetailsResponse(
                place_id=place_id,
                name=result.get("name") or "",
                formatted_address=result.get("formatted_address") or "",
                address_components=[
                    AddressComponent(
                        name=comp.get("long_name"), types=comp.get("types", [])
                    )
                    for comp in result.get("address_components", [])
                ],
                formatted_phone_number=result.get("formatted_phone_number"),
                geometry=Geometry(
                    location=Location(
                        latitude=result.get("geometry", {})
                        .get("location", {})
                        .get("lat"),
                        longitude=result.get("geometry", {})
                        .get("location", {})
                        .get("lng"),
                    ),
                    bounds=(
                        Bounds(
                            northeast=Location(
                                latitude=result.get("geometry", {})
                                .get("viewport", {})
                                .get("northeast", {})
                                .get("lat"),
                                longitude=result.get("geometry", {})
                                .get("viewport", {})
                                .get("northeast", {})
                                .get("lng"),
                            ),
                            southwest=Location(
                                latitude=result.get("geometry", {})
                                .get("viewport", {})
                                .get("southwest", {})
                                .get("lat"),
                                longitude=result.get("geometry", {})
                                .get("viewport", {})
                                .get("southwest", {})
                                .get("lng"),
                            ),
                        )
                        if result.get("geometry", {}).get("viewport")
                        else None
                    ),
                ),
                types=result.get("types", []),
                rating=result.get("rating"),
                user_ratings_total=result.get("user_ratings_total"),
                price_level=result.get("price_level"),
                opening_hours=(
                    OpeningHours(
                        open_now=result.get("opening_hours", {}).get("open_now", False),
                        periods=result.get("opening_hours", {}).get("periods", []),
                        weekday_text=result.get("opening_hours", {}).get(
                            "weekday_text", []
                        ),
                    )
                    if result.get("opening_hours")
                    else None
                ),
                website=result.get("website"),
                photos=(
                    [
                        PhotoInfo(
                            photo_url=await self.generate_place_photo_url(
                                photo.get("photo_reference")
                            ),
                            size=(photo.get("width"), photo.get("height")),
                        )
                        for photo in result.get("photos", [])[:5]  # Limit to first 5 photos
                        if photo.get("photo_reference")  # Only process photos with valid references
                    ]
                    if result.get("photos")
                    else None
                ),
                reviews=(
                    [
                        Review(rating=review.get("rating"), text=review.get("text"))
                        for review in result.get("reviews", [])
                    ]
                    if result.get("reviews")
                    else None
                ),
                utc_offset=result.get("utc_offset"),
                sustainable_certificate="Not Green Verified",
            )
        except httpx.ConnectError as e:
            print(f"Network connection error in get_place_details: {str(e)}")
            raise ValueError(f"Network connection error: Unable to reach Google Places API")
        except httpx.TimeoutException as e:
            print(f"Timeout error in get_place_details: {str(e)}")
            raise ValueError(f"Request timeout: Google Places API took too long to respond")
        except httpx.HTTPStatusError as e:
            print(f"HTTP error in get_place_details: {e.response.status_code} - {e.response.text}")
            raise ValueError(f"Google Places API error: {e.response.status_code}")
        except Exception as e:
            print(f"Error in get_place_details: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e

    async def reverse_geocode(
        self, location: Location, language: str = "vi"
    ) -> GeocodingResponse:
        try:
            params = {
                "latlng": f"{location.latitude},{location.longitude}",
                "language": language,
                "key": self.api_key,
            }

            url = f"{self.base_url}/geocode/json"
            response = await self.client.get(url, params=params)

            if response.status_code != 200:
                raise ValueError(
                    f"Error in reverse geocoding: HTTP {response.status_code}"
                )

            data = response.json()
            if data.get("status") != "OK":
                raise ValueError(f"Error in reverse geocoding: {data.get('status')}")

            results = []
            for result in data.get("results", []):
                results.append(
                    GeocodingResult(
                        place_id=result.get("place_id"),
                        formatted_address=result.get("formatted_address"),
                        address_components=[
                            AddressComponent(
                                name=comp.get("long_name"), types=comp.get("types", [])
                            )
                            for comp in result.get("address_components", [])
                        ],
                        geometry=Geometry(
                            location=Location(
                                latitude=result.get("geometry", {})
                                .get("location", {})
                                .get("lat"),
                                longitude=result.get("geometry", {})
                                .get("location", {})
                                .get("lng"),
                            ),
                            bounds=Bounds(
                                northeast=Location(
                                    latitude=result.get("geometry", {})
                                    .get("viewport", {})
                                    .get("northeast", {})
                                    .get("lat"),
                                    longitude=result.get("geometry", {})
                                    .get("viewport", {})
                                    .get("northeast", {})
                                    .get("lng"),
                                ),
                                southwest=Location(
                                    latitude=result.get("geometry", {})
                                    .get("viewport", {})
                                    .get("southwest", {})
                                    .get("lat"),
                                    longitude=result.get("geometry", {})
                                    .get("viewport", {})
                                    .get("southwest", {})
                                    .get("lng"),
                                ),
                            ),
                        ),
                        types=result.get("types", []),
                    )
                )

            return GeocodingResponse(results=results)
        except Exception as e:
            print(f"Error in reverse_geocode: {e}")
            raise e

    async def geocode(
        self, address: str, language: str = "vi", region: str = "vn"
    ) -> GeocodingResponse:
        try:
            params = {
                "address": address,
                "language": language,
                "region": region,
                "key": self.api_key,
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
                results.append(
                    GeocodingResult(
                        place_id=result.get("place_id"),
                        formatted_address=result.get("formatted_address"),
                        address_components=[
                            AddressComponent(
                                name=comp.get("long_name"), types=comp.get("types", [])
                            )
                            for comp in result.get("address_components", [])
                        ],
                        geometry=Geometry(
                            location=Location(
                                latitude=result.get("geometry", {})
                                .get("location", {})
                                .get("lat"),
                                longitude=result.get("geometry", {})
                                .get("location", {})
                                .get("lng"),
                            ),
                            bounds=Bounds(
                                northeast=Location(
                                    latitude=result.get("geometry", {})
                                    .get("viewport", {})
                                    .get("northeast", {})
                                    .get("lat"),
                                    longitude=result.get("geometry", {})
                                    .get("viewport", {})
                                    .get("northeast", {})
                                    .get("lng"),
                                ),
                                southwest=Location(
                                    latitude=result.get("geometry", {})
                                    .get("viewport", {})
                                    .get("southwest", {})
                                    .get("lat"),
                                    longitude=result.get("geometry", {})
                                    .get("viewport", {})
                                    .get("southwest", {})
                                    .get("lng"),
                                ),
                            ),
                        ),
                        types=result.get("types", []),
                    )
                )

            return GeocodingResponse(results=results)
        except Exception as e:
            print(f"Error in geocode: {e}")
            raise e

    async def get_nearby_places_for_map(
        self, data: NearbyPlaceRequest, language: str = "vi"
    ) -> NearbyPlacesResponse:
        try:
            params = {
                "location": f"{data.location.latitude},{data.location.longitude}",
                "radius": data.radius if data.radius else 3600,
                "rankby": data.rank_by,
                "language": language,
                "key": self.api_key,
            }
            if data.place_type:
                params["type"] = data.place_type
            if data.keyword:
                params["keyword"] = data.keyword

            url = f"{self.base_url}/place/nearbysearch/json"
            response = await self.client.get(url, params=params)

            if response.status_code != 200:
                raise ValueError(
                    f"Error fetching nearby places: HTTP {response.status_code}"
                )

            response_data = response.json()
            if response_data.get("status") != "OK":
                raise ValueError(
                    f"Error fetching nearby places: {response_data.get('status')}"
                )

            places = [
                NearbyPlaceSimple(
                    place_id=result["place_id"],
                    name=result["name"],
                    location=Location(
                        latitude=result["geometry"]["location"]["lat"],
                        longitude=result["geometry"]["location"]["lng"],
                    ),
                    rating=result.get("rating"),
                    types=result.get("types", []),
                )
                for result in response_data.get("results", [])
            ]

            return NearbyPlacesResponse(
                center=data.location,
                places=places,
                next_page_token=response_data.get("next_page_token"),
            )
        except Exception as e:
            print(f"Error in get_nearby_places_for_map: {e}")
            raise e

    async def get_next_page_nearby_places(
        self,
        page_token: str,
    ) -> NearbyPlacesResponse:
        try:
            params = {"pagetoken": page_token, "key": self.api_key}
            url = f"{self.base_url}/place/nearbysearch/json"
            response = await self.client.get(url, params=params)

            if response.status_code != 200:
                raise ValueError(
                    f"Error fetching next page of nearby places: HTTP {response.status_code}"
                )

            response_data = response.json()
            if response_data.get("status") != "OK":
                raise ValueError(
                    f"Error fetching next page of nearby places: {response_data.get('status')}"
                )
            places = [
                NearbyPlaceSimple(
                    place_id=result["place_id"],
                    name=result["name"],
                    location=Location(
                        latitude=result["geometry"]["location"]["lat"],
                        longitude=result["geometry"]["location"]["lng"],
                    ),
                    rating=result.get("rating"),
                    types=result.get("types", []),
                )
                for result in response_data.get("results", [])
            ]

            return NearbyPlacesResponse(
                center=None,
                places=places,
                next_page_token=response_data.get("next_page_token"),
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
            interpolate = await interpolate_search_params(
                distance=route.legs[0].distance
            )
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
                        location=point, radius=interpolate[0], place_type=search_type
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
            if not photo_reference:
                print("Warning: photo_reference is None or empty")
                return ""
            
            if photo_reference.startswith("places/"):
                base_url = f"https://places.googleapis.com/v1/{photo_reference}/media"

                params = {
                    "maxHeightPx": maxwidth,
                    "maxWidthPx": maxwidth,
                    "key": self.api_key,
                }

                request = self.client.build_request("GET", base_url, params=params)
                return str(request.url)

            else:
                params = {
                    "maxwidth": maxwidth,
                    "photoreference": photo_reference,
                    "key": self.api_key,
                }
                url = f"{self.base_url}/place/photo"
                request = self.client.build_request("GET", url, params=params)
                response = await self.client.send(request, follow_redirects=False)

                if response.status_code in (301, 302, 303, 307):
                    return response.headers.get("Location")
                else:
                    return str(response.url)

        except Exception as e:
            print(f"Error in generate_place_photo_url: {e}")
            raise e


async def create_map_client(api_key: Optional[str] = None) -> MapAPI:
    return MapAPI(api_key=api_key)
