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

class RouteAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GOOGLE_API_KEY
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        self.base_url = "https://routes.googleapis.com/directions/v2:computeRoutes"
        self.client = httpx.AsyncClient(timeout=10)
    
    async def close(self):
        await self.client.aclose()
        
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
            
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key,
                "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline,routes.legs,routes.viewport,routes.routeLabels"
            }
            
            response = await self.client.post(self.base_url, json=payload, headers=headers)
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
            
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key,
                "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline,routes.legs,routes.viewport,routes.routeLabels,routes.description"
            }
            
            response = await self.client.post(self.base_url, json=payload, headers=headers)
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


async def create_route_api_client(api_key: Optional[str] = None) -> RouteAPI:
    return RouteAPI(api_key=api_key)