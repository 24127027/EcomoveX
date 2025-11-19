import time
from typing import Any, Dict, List, Optional, Tuple
import httpx
from schemas.route_schema import *
from schemas.map_schema import *
from utils.config import settings
from utils.maps.map_utils import interpolate_search_params

TRANSPORT_MODE_TO_ROUTES_API = {
    "car": "DRIVE",
    "motorbike": "DRIVE",
    "walking": "WALK",
    "bus": "TRANSIT",
    "metro": "TRANSIT",
    "train": "TRANSIT"
}

class GoogleMapsAPI:   
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GOOGLE_API_KEY
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
    
    async def get_routes(
        self,
        data: DirectionsRequest,
        mode: TransportMode,
        language: str = "vi"
    ) -> DirectionsResponse:
        try:
            payload: Dict[str, Any] = {
                "origin": {
                    "location": {
                        "latLng": {
                            "latitude": data.origin[0],
                            "longitude": data.origin[1]
                        }
                    }
                },
                "destination": {
                    "location": {
                        "latLng": {
                            "latitude": data.destination[0],
                            "longitude": data.destination[1]
                        }
                    }
                },
                "travelMode": TRANSPORT_MODE_TO_ROUTES_API.get(mode.value, "DRIVE"),
                "languageCode": language,
                "computeAlternativeRoutes": data.alternatives,
            }
            
            if data.get_traffic:
                payload["departureTime"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            
            if data.waypoints:
                payload["intermediates"] = [
                    {
                        "location": {
                            "latLng": {
                                "latitude": wp[0],
                                "longitude": wp[1]
                            }
                        }
                    }
                    for wp in data.waypoints
                ]
                payload["optimizeWaypointOrder"] = True
            
            if data.avoid:
                route_modifiers = {}
                if "tolls" in data.avoid:
                    route_modifiers["avoidTolls"] = True
                if "highways" in data.avoid:
                    route_modifiers["avoidHighways"] = True
                if "ferries" in data.avoid:
                    route_modifiers["avoidFerries"] = True
                if route_modifiers:
                    payload["routeModifiers"] = route_modifiers
            
            url = "https://routes.googleapis.com/directions/v2:computeRoutes"
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key,
                "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline,routes.legs,routes.viewport,routes.routeLabels"
            }
            
            response = await self.client.post(url, json=payload, headers=headers)
            response_data = response.json()
            
            if response.status_code != 200:
                raise ValueError(f"Error fetching routes: {response_data}")
            
            routes = []
            for route_data in response_data.get("routes", []):
                legs = []
                for leg_data in route_data.get("legs", []):
                    steps = []
                    for step_data in leg_data.get("steps", []):
                        travel_mode_str = step_data.get("travelMode", "WALK")
                        if travel_mode_str == "DRIVE":
                            transport_mode = mode if mode in [TransportMode.car, TransportMode.motorbike] else TransportMode.car
                        elif travel_mode_str == "WALK":
                            transport_mode = TransportMode.walking
                        elif travel_mode_str == "TRANSIT":
                            transport_mode = mode if mode in [TransportMode.bus, TransportMode.metro, TransportMode.train] else TransportMode.bus
                        else:
                            transport_mode = TransportMode.walking
                        
                        start_loc = step_data.get("startLocation", {}).get("latLng", {})
                        end_loc = step_data.get("endLocation", {}).get("latLng", {})
                        
                        v = step_data.get("staticDuration", "0s")
                        seconds = 0.0
                        if isinstance(v, (int, float)):
                            seconds = float(v)
                        elif isinstance(v, dict):
                            if v.get("seconds") is not None:
                                try:
                                    seconds = float(v.get("seconds"))
                                except Exception:
                                    seconds = 0.0
                            elif v.get("value") is not None:
                                try:
                                    seconds = float(v.get("value"))
                                except Exception:
                                    seconds = 0.0
                        elif isinstance(v, str) and v.endswith("s"):
                            try:
                                seconds = float(v[:-1])
                            except Exception:
                                seconds = 0.0
                        duration_minutes = seconds / 60

                        steps.append(
                            Step(
                                distance=step_data.get("distanceMeters", 0) / 1000,
                                duration=duration_minutes,
                                start_location=(start_loc.get("latitude", 0), start_loc.get("longitude", 0)),
                                end_location=(end_loc.get("latitude", 0), end_loc.get("longitude", 0)),
                                html_instructions=step_data.get("navigationInstruction", {}).get("instructions", ""),
                                travel_mode=transport_mode,
                                polyline=step_data.get("polyline", {}).get("encodedPolyline"),
                                transit_details=step_data.get("transitDetails")
                            )
                        )
                    
                    start_loc = leg_data.get("startLocation", {}).get("latLng", {})
                    end_loc = leg_data.get("endLocation", {}).get("latLng", {})

                    v_leg = leg_data.get("duration", "0s")
                    leg_seconds = 0.0
                    if isinstance(v_leg, (int, float)):
                        leg_seconds = float(v_leg)
                    elif isinstance(v_leg, dict):
                        if v_leg.get("seconds") is not None:
                            try:
                                leg_seconds = float(v_leg.get("seconds"))
                            except Exception:
                                leg_seconds = 0.0
                        elif v_leg.get("value") is not None:
                            try:
                                leg_seconds = float(v_leg.get("value"))
                            except Exception:
                                leg_seconds = 0.0
                    elif isinstance(v_leg, str) and v_leg.endswith("s"):
                        try:
                            leg_seconds = float(v_leg[:-1])
                        except Exception:
                            leg_seconds = 0.0
                    leg_minutes = leg_seconds / 60

                    v_static = leg_data.get("staticDuration", "0s")
                    traffic_seconds = 0.0
                    if isinstance(v_static, (int, float)):
                        traffic_seconds = float(v_static)
                    elif isinstance(v_static, dict):
                        if v_static.get("seconds") is not None:
                            try:
                                traffic_seconds = float(v_static.get("seconds"))
                            except Exception:
                                traffic_seconds = 0.0
                        elif v_static.get("value") is not None:
                            try:
                                traffic_seconds = float(v_static.get("value"))
                            except Exception:
                                traffic_seconds = 0.0
                    elif isinstance(v_static, str) and v_static.endswith("s"):
                        try:
                            traffic_seconds = float(v_static[:-1])
                        except Exception:
                            traffic_seconds = 0.0
                    traffic_minutes = traffic_seconds / 60

                    leg = Leg(
                        distance=leg_data.get("distanceMeters", 0) / 1000,
                        duration=leg_minutes,
                        start_location=(
                            leg_data.get("startLocation", {}).get("address", ""),
                            (start_loc.get("latitude", 0), start_loc.get("longitude", 0))
                        ),
                        end_location=(
                            leg_data.get("endLocation", {}).get("address", ""),
                            (end_loc.get("latitude", 0), end_loc.get("longitude", 0))
                        ),
                        steps=steps,
                        duration_in_traffic=traffic_minutes if data.get_traffic else None,
                        arrival_time=leg_data.get("arrivalTime"),
                        departure_time=leg_data.get("departureTime")
                    )
                    legs.append(leg)
                
                viewport = route_data.get("viewport", {})
                ne = viewport.get("high", {})
                sw = viewport.get("low", {})
                
                v_route = route_data.get("duration", "0s")
                route_seconds = 0.0
                if isinstance(v_route, (int, float)):
                    route_seconds = float(v_route)
                elif isinstance(v_route, dict):
                    if v_route.get("seconds") is not None:
                        try:
                            route_seconds = float(v_route.get("seconds"))
                        except Exception:
                            route_seconds = 0.0
                    elif v_route.get("value") is not None:
                        try:
                            route_seconds = float(v_route.get("value"))
                        except Exception:
                            route_seconds = 0.0
                elif isinstance(v_route, str) and v_route.endswith("s"):
                    try:
                        route_seconds = float(v_route[:-1])
                    except Exception:
                        route_seconds = 0.0
                route_minutes = route_seconds / 60

                route = Route(
                    summary=" → ".join([leg.end_location[0] for leg in legs]) if legs else "",
                    legs=legs,
                    overview_polyline=route_data.get("polyline", {}).get("encodedPolyline", ""),
                    bounds=Bounds(
                        northeast=(ne.get("latitude", 0), ne.get("longitude", 0)),
                        southwest=(sw.get("latitude", 0), sw.get("longitude", 0))
                    ),
                    distance=sum(leg.distance for leg in legs),
                    duration=sum(leg.duration for leg in legs),
                    duration_in_traffic=route_minutes if data.get_traffic else None
                )
                routes.append(route)
            
            return DirectionsResponse(routes=routes, travel_mode=mode)
        except Exception as e:
            print(f"Error in get_routes: {e}")
            raise e
    
    
    async def get_eco_friendly_route(
        self,
        data: DirectionsRequest,
        mode: TransportMode,
        vehicle_type: str = "GASOLINE",  # GASOLINE, DIESEL, ELECTRIC, HYBRID
        language: str = "vi"
    ) -> DirectionsResponse:
        try:
            payload: Dict[str, Any] = {
                "origin": {
                    "location": {
                        "latLng": {
                            "latitude": data.origin[0],
                            "longitude": data.origin[1]
                        }
                    }
                },
                "destination": {
                    "location": {
                        "latLng": {
                            "latitude": data.destination[0],
                            "longitude": data.destination[1]
                        }
                    }
                },
                "travelMode": TRANSPORT_MODE_TO_ROUTES_API.get(mode.value, "DRIVE"),
                "languageCode": language,
                "computeAlternativeRoutes": True,
                "routingPreference": "FUEL_EFFICIENT",
            }
            
            if mode in [TransportMode.car, TransportMode.motorbike]:
                payload["vehicleInfo"] = {
                    "emissionType": vehicle_type
                }
            
            if data.get_traffic:
                payload["departureTime"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            
            if data.waypoints:
                payload["intermediates"] = [
                    {
                        "location": {
                            "latLng": {
                                "latitude": wp[0],
                                "longitude": wp[1]
                            }
                        }
                    }
                    for wp in data.waypoints
                ]
                payload["optimizeWaypointOrder"] = True
            
            route_modifiers = {}
            if data.avoid:
                if "tolls" in data.avoid:
                    route_modifiers["avoidTolls"] = True
                if "highways" in data.avoid:
                    route_modifiers["avoidHighways"] = True
                if "ferries" in data.avoid:
                    route_modifiers["avoidFerries"] = True
            if route_modifiers:
                payload["routeModifiers"] = route_modifiers
            
            url = "https://routes.googleapis.com/directions/v2:computeRoutes"
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key,
                "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline,routes.legs,routes.viewport,routes.routeLabels,routes.description"
            }
            
            response = await self.client.post(url, json=payload, headers=headers)
            response_data = response.json()
            
            if response.status_code != 200:
                raise ValueError(f"Error fetching eco-friendly routes: {response_data}")
            
            routes = []
            for route_data in response_data.get("routes", []):
                route_labels = route_data.get("routeLabels", [])
                is_eco = "ECO_FRIENDLY" in route_labels or "FUEL_EFFICIENT" in route_labels
                
                legs = []
                for leg_data in route_data.get("legs", []):
                    steps = []
                    for step_data in leg_data.get("steps", []):
                        travel_mode_str = step_data.get("travelMode", "WALK")
                        if travel_mode_str == "DRIVE":
                            transport_mode = mode if mode in [TransportMode.car, TransportMode.motorbike] else TransportMode.car
                        elif travel_mode_str == "WALK":
                            transport_mode = TransportMode.walking
                        elif travel_mode_str == "TRANSIT":
                            transport_mode = mode if mode in [TransportMode.bus, TransportMode.metro, TransportMode.train] else TransportMode.bus
                        else:
                            transport_mode = TransportMode.walking
                        
                        start_loc = step_data.get("startLocation", {}).get("latLng", {})
                        end_loc = step_data.get("endLocation", {}).get("latLng", {})
                        
                        v = step_data.get("staticDuration", "0s")
                        seconds = 0.0
                        if isinstance(v, (int, float)):
                            seconds = float(v)
                        elif isinstance(v, dict):
                            if v.get("seconds") is not None:
                                try:
                                    seconds = float(v.get("seconds"))
                                except Exception:
                                    seconds = 0.0
                            elif v.get("value") is not None:
                                try:
                                    seconds = float(v.get("value"))
                                except Exception:
                                    seconds = 0.0
                        elif isinstance(v, str) and v.endswith("s"):
                            try:
                                seconds = float(v[:-1])
                            except Exception:
                                seconds = 0.0
                        duration_minutes = seconds / 60

                        steps.append(
                            Step(
                                distance=step_data.get("distanceMeters", 0) / 1000,
                                duration=duration_minutes,
                                start_location=(start_loc.get("latitude", 0), start_loc.get("longitude", 0)),
                                end_location=(end_loc.get("latitude", 0), end_loc.get("longitude", 0)),
                                html_instructions=step_data.get("navigationInstruction", {}).get("instructions", ""),
                                travel_mode=transport_mode,
                                polyline=step_data.get("polyline", {}).get("encodedPolyline"),
                                transit_details=step_data.get("transitDetails")
                            )
                        )
                    
                    start_loc = leg_data.get("startLocation", {}).get("latLng", {})
                    end_loc = leg_data.get("endLocation", {}).get("latLng", {})
                    
                    v_leg = leg_data.get("duration", "0s")
                    leg_seconds = 0.0
                    if isinstance(v_leg, (int, float)):
                        leg_seconds = float(v_leg)
                    elif isinstance(v_leg, dict):
                        if v_leg.get("seconds") is not None:
                            try:
                                leg_seconds = float(v_leg.get("seconds"))
                            except Exception:
                                leg_seconds = 0.0
                        elif v_leg.get("value") is not None:
                            try:
                                leg_seconds = float(v_leg.get("value"))
                            except Exception:
                                leg_seconds = 0.0
                    elif isinstance(v_leg, str) and v_leg.endswith("s"):
                        try:
                            leg_seconds = float(v_leg[:-1])
                        except Exception:
                            leg_seconds = 0.0
                    leg_minutes = leg_seconds / 60

                    v_static = leg_data.get("staticDuration", "0s")
                    traffic_seconds = 0.0
                    if isinstance(v_static, (int, float)):
                        traffic_seconds = float(v_static)
                    elif isinstance(v_static, dict):
                        if v_static.get("seconds") is not None:
                            try:
                                traffic_seconds = float(v_static.get("seconds"))
                            except Exception:
                                traffic_seconds = 0.0
                        elif v_static.get("value") is not None:
                            try:
                                traffic_seconds = float(v_static.get("value"))
                            except Exception:
                                traffic_seconds = 0.0
                    elif isinstance(v_static, str) and v_static.endswith("s"):
                        try:
                            traffic_seconds = float(v_static[:-1])
                        except Exception:
                            traffic_seconds = 0.0
                    traffic_minutes = traffic_seconds / 60

                    leg = Leg(
                        distance=leg_data.get("distanceMeters", 0) / 1000,
                        duration=leg_minutes,
                        start_location=(
                            leg_data.get("startLocation", {}).get("address", ""),
                            (start_loc.get("latitude", 0), start_loc.get("longitude", 0))
                        ),
                        end_location=(
                            leg_data.get("endLocation", {}).get("address", ""),
                            (end_loc.get("latitude", 0), end_loc.get("longitude", 0))
                        ),
                        steps=steps,
                        duration_in_traffic=traffic_minutes if data.get_traffic else None,
                        arrival_time=leg_data.get("arrivalTime"),
                        departure_time=leg_data.get("departureTime")
                    )
                    legs.append(leg)
                
                viewport = route_data.get("viewport", {})
                ne = viewport.get("high", {})
                sw = viewport.get("low", {})
                
                description = route_data.get("description", "")
                summary = f"Eco-friendly: {description}" if is_eco else description or " → ".join([leg.end_location[0] for leg in legs]) if legs else ""
                
                v_route = route_data.get("duration", "0s")
                route_seconds = 0.0
                if isinstance(v_route, (int, float)):
                    route_seconds = float(v_route)
                elif isinstance(v_route, dict):
                    if v_route.get("seconds") is not None:
                        try:
                            route_seconds = float(v_route.get("seconds"))
                        except Exception:
                            route_seconds = 0.0
                    elif v_route.get("value") is not None:
                        try:
                            route_seconds = float(v_route.get("value"))
                        except Exception:
                            route_seconds = 0.0
                elif isinstance(v_route, str) and v_route.endswith("s"):
                    try:
                        route_seconds = float(v_route[:-1])
                    except Exception:
                        route_seconds = 0.0
                route_minutes = route_seconds / 60

                route = Route(
                    summary=summary,
                    legs=legs,
                    overview_polyline=route_data.get("polyline", {}).get("encodedPolyline", ""),
                    bounds=Bounds(
                        northeast=(ne.get("latitude", 0), ne.get("longitude", 0)),
                        southwest=(sw.get("latitude", 0), sw.get("longitude", 0))
                    ),
                    distance=sum(leg.distance for leg in legs),
                    duration=sum(leg.duration for leg in legs),
                    duration_in_traffic=route_minutes if data.get_traffic else None
                )
                routes.append(route)
            
            routes.sort(key=lambda r: ("Eco-friendly" not in r.summary, r.distance))
            
            return DirectionsResponse(routes=routes, travel_mode=mode)
        except Exception as e:
            print(f"Error in get_eco_friendly_route: {e}")
            raise e
    
    async def get_direction_for_multiple_modes(
        self,
        data: DirectionsRequest,
        modes: List[TransportMode]
    ) -> List[DirectionsResponse]:
        try:
            all_responses = []
            
            for mode in modes:
                directions = await self.get_routes(
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
            data = response.json()
            
            if data.get("status") != "OK":
                raise ValueError(f"Error fetching air quality data: {data.get('status')}")
            
            indexes = data.get("indexes", [])
            if not indexes:
                raise ValueError("No air quality index data available")
            
            primary_index = indexes[0]
            
            return AirQualityResponse(
                location=location,
                aqi_data=AirQualityIndex(
                    display_name=primary_index.get("displayName", "Air Quality Index"),
                    aqi=primary_index.get("aqi"),
                    category=primary_index.get("category")
                ),
                recommendations=HealthRecommendation(
                    general_population=data.get("healthRecommendations", {}).get("generalPopulation"),
                    sensitive_groups=data.get("healthRecommendations", {}).get("sensitiveGroups")
                ) if data.get("healthRecommendations") else None
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
        data: NearbyPlaceRequest,
        language: str = "vi"
    ) -> NearbyPlacesResponse:
        try:
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
                    location=(
                        result["geometry"]["location"]["lat"], 
                        result["geometry"]["location"]["lng"]
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
            response_data = response.json()
            if response_data.get("status") != "OK":
                raise ValueError(f"Error fetching next page of nearby places: {response_data.get('status')}")
            places = [
                NearbyPlaceSimple(
                    place_id=result["place_id"],
                    name=result["name"],
                    location=(
                        result["geometry"]["location"]["lat"],
                        result["geometry"]["location"]["lng"]
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
        data: DirectionsRequest,
        travel_mode: TransportMode,
        search_type: str,
    ) -> SearchAlongRouteResponse:
        directions = await self.get_routes(data=data, mode=travel_mode)        
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
            for place in data.places:  # Top 3 per point
                if place.place_id not in seen_place_ids:
                    seen_place_ids.add(place.place_id)
                    all_places.append(place)
        
        return SearchAlongRouteResponse(
            route_polyline=route.overview_polyline,
            places_along_route=all_places,
            search_type=search_type
        )

async def create_maps_client(api_key: Optional[str] = None) -> GoogleMapsAPI:
    return GoogleMapsAPI(api_key=api_key)