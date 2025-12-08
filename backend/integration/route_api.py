import time
from typing import Any, Dict, List, Optional

import httpx

from schemas.route_schema import (
    DirectionsRequest,
    DirectionsResponse,
    Leg,
    Route,
    Step,
    TransportMode,
)
from utils.config import settings

# Import Location and Bounds from route_schema since it already imports from destination_schema
from schemas.map_schema import Location

TRANSPORT_MODE_TO_ROUTES_API = {
    "car": "DRIVE",
    "motorbike": "DRIVE",
    "walking": "WALK",
    "bus": "TRANSIT",
    "metro": "TRANSIT",
    "train": "TRANSIT",
}


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate approximate distance between two coordinates in km (Haversine formula)."""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371  # Earth radius in km
    
    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c


def should_attempt_transit(origin: Location, destination: Location) -> tuple[bool, str]:
    """
    Check if transit route should be attempted based on distance and location.
    
    Returns:
        (should_try, reason)
    """
    distance = calculate_distance(
        origin.latitude, origin.longitude,
        destination.latitude, destination.longitude
    )
    
    # Too far for transit (>150km typically no public transit)
    if distance > 150:
        return False, f"Distance too far for public transit ({distance:.1f} km > 150 km)"
    
    # Very short distance (<500m), walking is better
    if distance < 0.5:
        return False, f"Distance too short for transit ({distance:.1f} km < 0.5 km), walking recommended"
    
    # Check if within major urban areas (simplified check)
    # Vietnam major cities: HCMC (10.7-10.9, 106.6-106.9), Hanoi (20.9-21.1, 105.7-105.9)
    in_hcmc = (10.7 <= origin.latitude <= 10.9 and 106.6 <= origin.longitude <= 106.9) or \
              (10.7 <= destination.latitude <= 10.9 and 106.6 <= destination.longitude <= 106.9)
    in_hanoi = (20.9 <= origin.latitude <= 21.1 and 105.7 <= origin.longitude <= 105.9) or \
               (20.9 <= destination.latitude <= 21.1 and 105.7 <= destination.longitude <= 105.9)
    
    if not (in_hcmc or in_hanoi):
        return True, f"Warning: Location may be outside major transit coverage (distance: {distance:.1f} km)"
    
    return True, f"Transit may be available (distance: {distance:.1f} km, in major city)"


class RouteAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GOOGLE_API_KEY
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        self.base_url = "https://routes.googleapis.com/directions/v2:computeRoutes"
        self.base_url_v1 = "https://maps.googleapis.com/maps/api/directions/json"
        self.client = httpx.AsyncClient(timeout=30.0)  # Increased timeout for Routes API

    @staticmethod
    def _parse_transit_details(transit_data: Dict[str, Any]) -> Optional[Any]:
        """Parse Google Routes API transitDetails into TransitStepDetail schema."""
        if not transit_data:
            return None
        
        try:
            from schemas.route_schema import TransitStepDetail
            
            stop_details = transit_data.get("stopDetails", {})
            arrival_stop = stop_details.get("arrivalStop", {})
            departure_stop = stop_details.get("departureStop", {})
            
            # Extract location from stops
            arrival_location = arrival_stop.get("location", {}).get("latLng", {})
            departure_location = departure_stop.get("location", {}).get("latLng", {})
            
            # Extract transit line info
            transit_line = transit_data.get("transitLine", {})
            line_name = (
                transit_line.get("nameShort") or 
                transit_line.get("name") or 
                "N/A"
            )
            
            return TransitStepDetail(
                arrival_stop=(
                    arrival_stop.get("name", ""),
                    Location(
                        latitude=arrival_location.get("latitude", 0),
                        longitude=arrival_location.get("longitude", 0),
                    ),
                ),
                departure_stop=(
                    departure_stop.get("name", ""),
                    Location(
                        latitude=departure_location.get("latitude", 0),
                        longitude=departure_location.get("longitude", 0),
                    ),
                ),
                arrival_time=stop_details.get("arrivalTime", {}),
                departure_time=stop_details.get("departureTime", {}),
                headway=transit_data.get("headsign"),
                line=line_name,
            )
        except Exception as e:
            print(f"Warning: Failed to parse transit details: {e}")
            return None

    async def close(self):
        await self.client.aclose()

    async def get_routes_v1(
        self, data: DirectionsRequest, mode: TransportMode, language: str = "vi"
    ) -> DirectionsResponse:
        """Use Directions API v1 for TRANSIT mode (better coverage in Vietnam)."""
        try:
            # Check if transit is feasible for this route
            if mode in [TransportMode.bus, TransportMode.metro, TransportMode.train]:
                should_try, reason = should_attempt_transit(data.origin, data.destination)
                print(f"Transit feasibility check: {reason}")
                if not should_try:
                    print(f"⚠️  Skipping transit request: {reason}")
                    raise ValueError(f"TRANSIT_NOT_FEASIBLE: {reason}")
            
            params = {
                "origin": f"{data.origin.latitude},{data.origin.longitude}",
                "destination": f"{data.destination.latitude},{data.destination.longitude}",
                "mode": TRANSPORT_MODE_TO_ROUTES_API.get(mode.value, "DRIVING").lower(),
                "language": language,
                "alternatives": "true" if data.alternatives else "false",
                "key": self.api_key,
            }

            if data.get_traffic:
                params["departure_time"] = "now"

            if data.waypoints:
                waypoints_str = "|".join([f"{wp[0]},{wp[1]}" for wp in data.waypoints])
                params["waypoints"] = f"optimize:true|{waypoints_str}"

            if data.avoid:
                avoid_list = []
                if "tolls" in data.avoid:
                    avoid_list.append("tolls")
                if "highways" in data.avoid:
                    avoid_list.append("highways")
                if "ferries" in data.avoid:
                    avoid_list.append("ferries")
                if avoid_list:
                    params["avoid"] = "|".join(avoid_list)

            print(f"\n=== Calling Google Directions API v1 ===")
            print(f"Mode: {mode.value}")
            print(f"Origin: ({data.origin.latitude}, {data.origin.longitude})")
            print(f"Destination: ({data.destination.latitude}, {data.destination.longitude})")

            response = await self.client.get(self.base_url_v1, params=params)

            print(f"Response Status: {response.status_code}")

            if response.status_code != 200:
                error_detail = response.text[:500] if response.text else "No error details"
                print(f"Directions API v1 HTTP Error {response.status_code}: {error_detail}")
                raise ValueError(f"Error fetching routes: HTTP {response.status_code} - {error_detail}")

            response_data = response.json()
            api_status = response_data.get('status')
            print(f"API Status: {api_status}")

            if api_status != "OK":
                error_msg = response_data.get("error_message", "")
                print(f"API Error Message: {error_msg}")
                
                if api_status == "ZERO_RESULTS":
                    print(f"❌ No transit routes available for this location")
                    print(f"   Possible reasons:")
                    print(f"   - Area not covered by public transit")
                    print(f"   - Rural/suburban area without bus service")
                    print(f"   - Distance too far for transit (>100km)")
                    print(f"   - No transit data in Google Maps")
                    raise ValueError(
                        f"TRANSIT_NOT_AVAILABLE: No public transit routes found between these locations. "
                        f"This area may not have bus/metro coverage or the distance is too far for transit."
                    )
                elif api_status == "NOT_FOUND":
                    raise ValueError(f"INVALID_LOCATION: One or both locations could not be geocoded. {error_msg}")
                elif api_status == "REQUEST_DENIED":
                    raise ValueError(f"API_ERROR: Request denied. Check API key and billing. {error_msg}")
                elif api_status == "INVALID_REQUEST":
                    raise ValueError(f"INVALID_REQUEST: The request parameters are invalid. {error_msg}")
                elif api_status == "OVER_QUERY_LIMIT":
                    raise ValueError(f"QUOTA_EXCEEDED: API quota exceeded. {error_msg}")
                else:
                    raise ValueError(f"API_ERROR: {api_status} - {error_msg}")

            routes = []
            for route_data in response_data.get("routes", []):
                legs = []
                for leg_data in route_data.get("legs", []):
                    steps = []
                    for step_data in leg_data.get("steps", []):
                        travel_mode_str = step_data.get("travel_mode", "WALKING").upper()
                        if travel_mode_str == "DRIVING":
                            transport_mode = mode if mode in [TransportMode.car, TransportMode.motorbike] else TransportMode.car
                        elif travel_mode_str == "WALKING":
                            transport_mode = TransportMode.walking
                        elif travel_mode_str == "TRANSIT":
                            transport_mode = mode if mode in [TransportMode.bus, TransportMode.metro, TransportMode.train] else TransportMode.bus
                        else:
                            transport_mode = TransportMode.walking

                        start_loc = step_data.get("start_location", {})
                        end_loc = step_data.get("end_location", {})

                        # Parse transit details if available
                        transit_details = None
                        if "transit_details" in step_data:
                            td = step_data["transit_details"]
                            from schemas.route_schema import TransitStepDetail
                            
                            arrival_stop = td.get("arrival_stop", {})
                            departure_stop = td.get("departure_stop", {})
                            line = td.get("line", {})
                            
                            transit_details = TransitStepDetail(
                                arrival_stop=(
                                    arrival_stop.get("name", ""),
                                    Location(
                                        latitude=arrival_stop.get("location", {}).get("lat", 0),
                                        longitude=arrival_stop.get("location", {}).get("lng", 0),
                                    ),
                                ),
                                departure_stop=(
                                    departure_stop.get("name", ""),
                                    Location(
                                        latitude=departure_stop.get("location", {}).get("lat", 0),
                                        longitude=departure_stop.get("location", {}).get("lng", 0),
                                    ),
                                ),
                                arrival_time=td.get("arrival_time", {}),
                                departure_time=td.get("departure_time", {}),
                                headway=td.get("headsign"),
                                line=line.get("short_name") or line.get("name", "N/A"),
                            )

                        steps.append(
                            Step(
                                distance=step_data.get("distance", {}).get("value", 0) / 1000,
                                duration=step_data.get("duration", {}).get("value", 0) / 60,
                                start_location=Location(
                                    latitude=start_loc.get("lat", 0),
                                    longitude=start_loc.get("lng", 0),
                                ),
                                end_location=Location(
                                    latitude=end_loc.get("lat", 0),
                                    longitude=end_loc.get("lng", 0),
                                ),
                                html_instructions=step_data.get("html_instructions", ""),
                                travel_mode=transport_mode,
                                polyline=step_data.get("polyline", {}).get("points"),
                                transit_details=transit_details,
                            )
                        )

                    start_loc = leg_data.get("start_location", {})
                    end_loc = leg_data.get("end_location", {})

                    leg = Leg(
                        distance=leg_data.get("distance", {}).get("value", 0) / 1000,
                        duration=leg_data.get("duration", {}).get("value", 0) / 60,
                        start_location=(
                            leg_data.get("start_address", ""),
                            Location(
                                latitude=start_loc.get("lat", 0),
                                longitude=start_loc.get("lng", 0),
                            ),
                        ),
                        end_location=(
                            leg_data.get("end_address", ""),
                            Location(
                                latitude=end_loc.get("lat", 0),
                                longitude=end_loc.get("lng", 0),
                            ),
                        ),
                        steps=steps,
                        duration_in_traffic=leg_data.get("duration_in_traffic", {}).get("value", 0) / 60 if data.get_traffic and "duration_in_traffic" in leg_data else None,
                        arrival_time=leg_data.get("arrival_time"),
                        departure_time=leg_data.get("departure_time"),
                    )
                    legs.append(leg)

                from schemas.destination_schema import Bounds
                
                bounds_data = route_data.get("bounds", {})
                ne = bounds_data.get("northeast", {})
                sw = bounds_data.get("southwest", {})

                route = Route(
                    summary=route_data.get("summary", ""),
                    legs=legs,
                    overview_polyline=route_data.get("overview_polyline", {}).get("points", ""),
                    bounds=Bounds(
                        northeast=Location(
                            latitude=ne.get("lat", 0),
                            longitude=ne.get("lng", 0),
                        ),
                        southwest=Location(
                            latitude=sw.get("lat", 0),
                            longitude=sw.get("lng", 0),
                        ),
                    ),
                    distance=sum(leg.distance for leg in legs),
                    duration=sum(leg.duration for leg in legs),
                    duration_in_traffic=sum(leg.duration_in_traffic for leg in legs if leg.duration_in_traffic) if data.get_traffic else None,
                )
                routes.append(route)

            print(f"Found {len(routes)} routes")
            return DirectionsResponse(routes=routes, travel_mode=mode)

        except Exception as e:
            print(f"Error in get_routes_v1: {e}")
            raise e

    async def get_routes(
        self, data: DirectionsRequest, mode: TransportMode, language: str = "vi"
    ) -> DirectionsResponse:
        # Use Directions v1 for TRANSIT mode (better coverage in Vietnam)
        if mode in [TransportMode.bus, TransportMode.metro, TransportMode.train]:
            return await self.get_routes_v1(data, mode, language)
        
        # Use Routes v2 for DRIVE and WALK
        try:
            payload: Dict[str, Any] = {
                "origin": {
                    "location": {
                        "latLng": {
                            "latitude": data.origin.latitude,
                            "longitude": data.origin.longitude,
                        }
                    }
                },
                "destination": {
                    "location": {
                        "latLng": {
                            "latitude": data.destination.latitude,
                            "longitude": data.destination.longitude,
                        }
                    }
                },
                "travelMode": TRANSPORT_MODE_TO_ROUTES_API.get(mode.value, "DRIVE"),
                "languageCode": language,
                "computeAlternativeRoutes": data.alternatives,
            }

            if data.get_traffic:
                payload["departureTime"] = time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                )

            if data.waypoints:
                payload["intermediates"] = [
                    {"location": {"latLng": {"latitude": wp[0], "longitude": wp[1]}}}
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
                "X-Goog-FieldMask": (
                    "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline,routes.legs,routes.viewport,routes.routeLabels"
                ),
            }

            print(f"\n=== Calling Google Routes API ===")
            print(f"Mode: {mode.value}")
            print(f"Travel Mode: {TRANSPORT_MODE_TO_ROUTES_API.get(mode.value, 'DRIVE')}")
            print(f"Origin: ({data.origin.latitude}, {data.origin.longitude})")
            print(f"Destination: ({data.destination.latitude}, {data.destination.longitude})")

            response = await self.client.post(
                self.base_url, json=payload, headers=headers
            )

            print(f"Response Status: {response.status_code}")
            
            if response.status_code != 200:
                error_detail = response.text[:500] if response.text else "No error details"
                print(f"Routes API HTTP Error {response.status_code}: {error_detail}")
                raise ValueError(f"Error fetching routes: HTTP {response.status_code} - {error_detail}")

            response_data = response.json()
            print(f"Response has routes: {bool(response_data.get('routes'))}")
            
            # Check if response is completely empty
            if not response_data:
                print(f"WARNING: Google Routes API returned empty response")
                print(f"This may indicate:")
                print(f"  1. Routes API not enabled in Google Cloud Console")
                print(f"  2. Billing not set up")
                print(f"  3. API quota exceeded")
                print(f"  4. Invalid API key")
                raise ValueError(f"Empty response from Routes API. Check API configuration.")
            
            if not response_data.get("routes"):
                print(f"\n=== No Routes Found ===")
                print(f"Request payload: {payload}")
                print(f"Response data: {response_data}")
                
                # Check for specific error messages
                if 'error' in response_data:
                    error_info = response_data['error']
                    error_msg = error_info.get('message', 'No error message')
                    error_code = error_info.get('code', 'No code')
                    error_status = error_info.get('status', 'No status')
                    print(f"API Error Code: {error_code}")
                    print(f"API Error Status: {error_status}")
                    print(f"API Error Message: {error_msg}")
                    raise ValueError(f"Routes API error: {error_msg} (code: {error_code})")
                else:
                    # Empty routes without error - likely mode not supported
                    if TRANSPORT_MODE_TO_ROUTES_API.get(mode.value) == 'TRANSIT':
                        print(f"TRANSIT mode may not be available for this route")
                        raise ValueError(f"TRANSIT routes not available for this location")
                    raise ValueError(f"No routes found without error message")

            routes = []
            for route_data in response_data.get("routes", []):
                legs = []
                for leg_data in route_data.get("legs", []):
                    steps = []
                    for step_data in leg_data.get("steps", []):
                        travel_mode_str = step_data.get("travelMode", "WALK")
                        if travel_mode_str == "DRIVE":
                            transport_mode = (
                                mode
                                if mode in [TransportMode.car, TransportMode.motorbike]
                                else TransportMode.car
                            )
                        elif travel_mode_str == "WALK":
                            transport_mode = TransportMode.walking
                        elif travel_mode_str == "TRANSIT":
                            transport_mode = (
                                mode
                                if mode
                                in [
                                    TransportMode.bus,
                                    TransportMode.metro,
                                    TransportMode.train,
                                ]
                                else TransportMode.bus
                            )
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
                                start_location=Location(
                                    latitude=start_loc.get("latitude", 0),
                                    longitude=start_loc.get("longitude", 0),
                                ),
                                end_location=Location(
                                    latitude=end_loc.get("latitude", 0),
                                    longitude=end_loc.get("longitude", 0),
                                ),
                                html_instructions=step_data.get(
                                    "navigationInstruction", {}
                                ).get("instructions", ""),
                                travel_mode=transport_mode,
                                polyline=step_data.get("polyline", {}).get(
                                    "encodedPolyline"
                                ),
                                transit_details=RouteAPI._parse_transit_details(
                                    step_data.get("transitDetails")
                                ),
                            )
                        )

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
                            Location(
                                latitude=start_loc.get("latitude", 0),
                                longitude=start_loc.get("longitude", 0),
                            ),
                        ),
                        end_location=(
                            leg_data.get("endLocation", {}).get("address", ""),
                            Location(
                                latitude=end_loc.get("latitude", 0),
                                longitude=end_loc.get("longitude", 0),
                            ),
                        ),
                        steps=steps,
                        duration_in_traffic=(
                            traffic_minutes if data.get_traffic else None
                        ),
                        arrival_time=leg_data.get("arrivalTime"),
                        departure_time=leg_data.get("departureTime"),
                    )
                    legs.append(leg)

                from schemas.destination_schema import Bounds
                
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
                    summary=(
                        " → ".join([leg.end_location[0] for leg in legs])
                        if legs
                        else ""
                    ),
                    legs=legs,
                    overview_polyline=route_data.get("polyline", {}).get(
                        "encodedPolyline", ""
                    ),
                    bounds=Bounds(
                        northeast=Location(
                            latitude=ne.get("latitude", 0),
                            longitude=ne.get("longitude", 0),
                        ),
                        southwest=Location(
                            latitude=sw.get("latitude", 0),
                            longitude=sw.get("longitude", 0),
                        ),
                    ),
                    distance=sum(leg.distance for leg in legs),
                    duration=sum(leg.duration for leg in legs),
                    duration_in_traffic=route_minutes if data.get_traffic else None,
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
        vehicle_type: str = "GASOLINE",  # Not used in API v2, kept for compatibility
        language: str = "vi",
    ) -> DirectionsResponse:
        """
        Get eco-friendly routes using TRAFFIC_AWARE_OPTIMAL preference.
        
        Note: Google Routes API v2 doesn't always return explicit eco labels.
        The actual eco-friendliness is determined by:
        1. TRAFFIC_AWARE_OPTIMAL routing preference (optimizes for efficiency)
        2. Carbon emission calculation in the service layer
        3. Comparison of multiple route alternatives
        
        The route with lowest carbon emission will be identified as the eco route.
        """
        try:
            payload: Dict[str, Any] = {
                "origin": {
                    "location": {
                        "latLng": {
                            "latitude": data.origin.latitude,
                            "longitude": data.origin.longitude,
                        }
                    }
                },
                "destination": {
                    "location": {
                        "latLng": {
                            "latitude": data.destination.latitude,
                            "longitude": data.destination.longitude,
                        }
                    }
                },
                "travelMode": TRANSPORT_MODE_TO_ROUTES_API.get(mode.value, "DRIVE"),
                "languageCode": language,
                "computeAlternativeRoutes": True,
                "routingPreference": "TRAFFIC_AWARE_OPTIMAL",  # Changed from FUEL_EFFICIENT
            }

            # Note: vehicleInfo is not supported in Routes API v2
            # Eco-friendly routes are identified by routeLabels instead

            if data.get_traffic:
                payload["departureTime"] = time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                )

            if data.waypoints:
                payload["intermediates"] = [
                    {"location": {"latLng": {"latitude": wp[0], "longitude": wp[1]}}}
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
                "X-Goog-FieldMask": (
                    "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline,routes.legs,routes.viewport,routes.routeLabels,routes.description"
                ),
            }

            response = await self.client.post(
                self.base_url, json=payload, headers=headers
            )

            if response.status_code != 200:
                raise ValueError(
                    f"Error fetching eco-friendly routes: HTTP {response.status_code}"
                )

            response_data = response.json()
            if not response_data.get("routes"):
                raise ValueError("No routes found in response")

            routes = []
            for route_data in response_data.get("routes", []):
                route_labels = route_data.get("routeLabels", [])
                is_eco = (
                    "ECO_FRIENDLY" in route_labels or "FUEL_EFFICIENT" in route_labels
                )

                legs = []
                for leg_data in route_data.get("legs", []):
                    steps = []
                    for step_data in leg_data.get("steps", []):
                        travel_mode_str = step_data.get("travelMode", "WALK")
                        if travel_mode_str == "DRIVE":
                            transport_mode = (
                                mode
                                if mode in [TransportMode.car, TransportMode.motorbike]
                                else TransportMode.car
                            )
                        elif travel_mode_str == "WALK":
                            transport_mode = TransportMode.walking
                        elif travel_mode_str == "TRANSIT":
                            transport_mode = (
                                mode
                                if mode
                                in [
                                    TransportMode.bus,
                                    TransportMode.metro,
                                    TransportMode.train,
                                ]
                                else TransportMode.bus
                            )
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
                                start_location=Location(
                                    latitude=start_loc.get("latitude", 0),
                                    longitude=start_loc.get("longitude", 0),
                                ),
                                end_location=Location(
                                    latitude=end_loc.get("latitude", 0),
                                    longitude=end_loc.get("longitude", 0),
                                ),
                                html_instructions=step_data.get(
                                    "navigationInstruction", {}
                                ).get("instructions", ""),
                                travel_mode=transport_mode,
                                polyline=step_data.get("polyline", {}).get(
                                    "encodedPolyline"
                                ),
                                transit_details=RouteAPI._parse_transit_details(
                                    step_data.get("transitDetails")
                                ),
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
                            Location(
                                latitude=start_loc.get("latitude", 0),
                                longitude=start_loc.get("longitude", 0),
                            ),
                        ),
                        end_location=(
                            leg_data.get("endLocation", {}).get("address", ""),
                            Location(
                                latitude=end_loc.get("latitude", 0),
                                longitude=end_loc.get("longitude", 0),
                            ),
                        ),
                        steps=steps,
                        duration_in_traffic=(
                            traffic_minutes if data.get_traffic else None
                        ),
                        arrival_time=leg_data.get("arrivalTime"),
                        departure_time=leg_data.get("departureTime"),
                    )
                    legs.append(leg)

                from schemas.destination_schema import Bounds
                
                viewport = route_data.get("viewport", {})
                ne = viewport.get("high", {})
                sw = viewport.get("low", {})

                description = route_data.get("description", "")
                summary = (
                    f"Eco-friendly: {description}"
                    if is_eco
                    else (
                        description or " → ".join([leg.end_location[0] for leg in legs])
                        if legs
                        else ""
                    )
                )

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
                    overview_polyline=route_data.get("polyline", {}).get(
                        "encodedPolyline", ""
                    ),
                    bounds=Bounds(
                        northeast=Location(
                            latitude=ne.get("latitude", 0),
                            longitude=ne.get("longitude", 0),
                        ),
                        southwest=Location(
                            latitude=sw.get("latitude", 0),
                            longitude=sw.get("longitude", 0),
                        ),
                    ),
                    distance=sum(leg.distance for leg in legs),
                    duration=sum(leg.duration for leg in legs),
                    duration_in_traffic=route_minutes if data.get_traffic else None,
                )
                routes.append(route)

            routes.sort(key=lambda r: ("Eco-friendly" not in r.summary, r.distance))

            return DirectionsResponse(routes=routes, travel_mode=mode)
        except Exception as e:
            print(f"Error in get_eco_friendly_route: {e}")
            raise e

    async def get_direction_for_multiple_modes(
        self, data: DirectionsRequest, modes: List[TransportMode]
    ) -> List[DirectionsResponse]:
        try:
            all_responses = []

            for mode in modes:
                directions = await self.get_routes(data=data, mode=mode)
                all_responses.append(directions)

            return all_responses
        except Exception as e:
            print(f"Error in get_direction_for_multiple_modes: {e}")
            raise e


async def create_route_api_client(api_key: Optional[str] = None) -> RouteAPI:
    return RouteAPI(api_key=api_key)
