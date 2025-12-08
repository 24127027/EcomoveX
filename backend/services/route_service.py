from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from schemas.map_schema import Location
from integration.route_api import create_route_api_client
from integration.text_generator_api import create_text_generator_api
from services.map_service import MapService
from schemas.route_schema import (
    DirectionsRequest,
    DirectionsResponse,
    FindRoutesRequest,
    FindRoutesResponse,
    RecommendResponse,
    RouteData,
    RouteType,
    TransitDetails,
    TransitStep,
    TransportMode,
    TripMetricsResponse,
    WalkingStep,
    RouteForPlanResponse,
)
from services.carbon_service import CarbonService
from services.map_service import MapService
from models.plan import PlanDestination
import math


class RouteService:
    @staticmethod
    def extract_transit_details(leg: Dict[str, Any]) -> TransitDetails:
        """
        Extract transit details from route leg.
        Handles format after model_dump() where distance/duration are already floats.
        """
        try:
            if not leg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Leg data is required",
                )

            transit_steps = []
            walking_steps = []

            steps = leg.get("steps", [])
            
            for step in steps:
                if not isinstance(step, dict):
                    continue
                    
                travel_mode = step.get("travel_mode")
                if not travel_mode:
                    continue
                
                # Normalize travel_mode to string
                if hasattr(travel_mode, 'value'):
                    travel_mode = travel_mode.value
                travel_mode = str(travel_mode).upper()
                
                # Extract common fields (after model_dump(), these are already simple types)
                distance = step.get("distance", 0)  # Already float in km
                duration = step.get("duration", 0)  # Already float in minutes
                
                # Handle TRANSIT steps
                if travel_mode in ["TRANSIT", "BUS", "METRO", "TRAIN"]:
                    transit_details_data = step.get("transit_details")
                    if not transit_details_data or not isinstance(transit_details_data, dict):
                        continue
                    
                    # Extract line name (can be string or dict)
                    line = transit_details_data.get("line", "N/A")
                    if isinstance(line, dict):
                        line = line.get("short_name") or line.get("name", "N/A")
                    
                    # Extract stop locations (after model_dump, these are tuples or dicts)
                    departure_stop = transit_details_data.get("departure_stop", [])
                    arrival_stop = transit_details_data.get("arrival_stop", [])
                    
                    # Parse stop format: can be tuple (name, Location) or dict
                    dep_lat, dep_lng = 0.0, 0.0
                    arr_lat, arr_lng = 0.0, 0.0
                    
                    if isinstance(departure_stop, (list, tuple)) and len(departure_stop) >= 2:
                        dep_location = departure_stop[1]
                        if isinstance(dep_location, dict):
                            dep_lat = dep_location.get("latitude", 0.0)
                            dep_lng = dep_location.get("longitude", 0.0)
                    
                    if isinstance(arrival_stop, (list, tuple)) and len(arrival_stop) >= 2:
                        arr_location = arrival_stop[1]
                        if isinstance(arr_location, dict):
                            arr_lat = arr_location.get("latitude", 0.0)
                            arr_lng = arr_location.get("longitude", 0.0)
                    
                    transit_steps.append({
                        "line": line,
                        "vehicle": TransportMode.bus,
                        "departure_stop": {
                            "lat": dep_lat,
                            "lng": dep_lng,
                        },
                        "arrival_stop": {
                            "lat": arr_lat,
                            "lng": arr_lng,
                        },
                        "num_stops": 0,  # v1 API doesn't provide this
                        "duration": duration if isinstance(duration, (int, float)) else 0,
                    })
                
                # Handle WALKING steps
                elif travel_mode in ["WALKING", "WALK"]:
                    # Distance is already in km, convert to meters for schema
                    distance_m = distance * 1000 if isinstance(distance, (int, float)) else 0
                    duration_min = duration if isinstance(duration, (int, float)) else 0
                    
                    walking_steps.append({
                        "distance": distance_m,
                        "duration": duration_min,
                        "instruction": step.get("html_instructions", ""),
                    })

            return TransitDetails(
                transit_steps=[TransitStep(**step) for step in transit_steps],
                walking_steps=[WalkingStep(**step) for step in walking_steps],
                total_transit_steps=len(transit_steps),
                total_walking_steps=len(walking_steps),
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to extract transit details: {str(e)}",
            )

    @staticmethod
    async def process_route_data(
        route: Dict[str, Any],
        mode: TransportMode,
        route_type: RouteType,
    ) -> RouteData:
        try:
            if not route or "legs" not in route or not route["legs"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid route data: missing legs information",
                )

            leg = route["legs"][0]
            distance_km = leg["distance"]
            duration_min = leg["duration"]

            carbon_response = await CarbonService.estimate_transport_emission(
                mode, distance_km
            )

            result = RouteData(
                type=route_type,
                mode=[mode],
                distance=distance_km,
                duration=duration_min,
                carbon=carbon_response,
                route_details=route,
            )

            if mode in [TransportMode.bus, TransportMode.metro, TransportMode.train]:
                try:
                    result.transit_info = RouteService.extract_transit_details(leg)
                except Exception as e:
                    print(f"WARNING: Failed to extract transit details: {e}")
                    # Set empty transit info instead of failing
                    result.transit_info = TransitDetails(
                        transit_steps=[],
                        walking_steps=[],
                        total_transit_steps=0,
                        total_walking_steps=0,
                    )

            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process route data: {str(e)}",
            )

    @staticmethod
    async def find_three_optimal_routes(
        request: FindRoutesRequest,
    ) -> FindRoutesResponse:
        try:
            origin = request.origin
            destination = request.destination
            max_time_ratio = request.max_time_ratio
            language = request.language

            if not origin or not destination:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Origin and destination are required",
                )

            if max_time_ratio <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="max_time_ratio must be greater than 0",
                )

            routes_dict = {}

            try:
                routes = await create_route_api_client()

                driving_alternatives = await routes.get_routes(
                    data=DirectionsRequest(
                        origin=origin, destination=destination, alternatives=True
                    ),
                    mode=TransportMode.car,
                    language=language,
                )

                # Try to get transit routes, but don't fail if unavailable
                transit_result = None
                try:
                    transit_result = await routes.get_routes(
                        data=DirectionsRequest(
                            origin=origin, destination=destination, alternatives=True
                        ),
                        mode=TransportMode.bus,
                        language=language,
                    )
                except Exception as e:
                    print(f"Transit routes not available: {str(e)}")
                    transit_result = DirectionsResponse(routes=[])

                walking_result = await routes.get_routes(
                    data=DirectionsRequest(origin=origin, destination=destination),
                    mode=TransportMode.walking,
                    language=language,
                )

                all_routes = []

                if driving_alternatives.routes:
                    for idx, route in enumerate(driving_alternatives.routes):
                        route_type = (
                            RouteType.fastest if idx == 0 else RouteType.fastest
                        )

                        route_data = await RouteService.process_route_data(
                            route.model_dump(), TransportMode.car, route_type
                        )
                        all_routes.append(route_data)

                # Get eco-friendly routes using TRAFFIC_AWARE_OPTIMAL
                # Note: Google may not return explicit eco labels, but this preference
                # optimizes for fuel efficiency
                try:
                    eco_result = await routes.get_eco_friendly_route(
                        data=DirectionsRequest(
                            origin=origin, destination=destination, alternatives=True
                        ),
                        mode=TransportMode.car,
                        vehicle_type="GASOLINE",
                        language=language,
                    )
                    
                    # Process eco routes and add to all_routes
                    # The actual "eco-friendliness" will be determined by carbon calculation
                    if eco_result and eco_result.routes:
                        for eco_route in eco_result.routes:
                            eco_route_data = await RouteService.process_route_data(
                                eco_route.model_dump(), TransportMode.car, RouteType.low_carbon
                            )
                            # Only add if not duplicate (check by distance + duration)
                            is_duplicate = any(
                                abs(r.distance - eco_route_data.distance) < 0.1 and
                                abs(r.duration - eco_route_data.duration) < 1
                                for r in all_routes
                            )
                            if not is_duplicate:
                                all_routes.append(eco_route_data)
                except Exception as e:
                    print(f"Eco route request failed (will use carbon-based selection): {str(e)}")
                    eco_result = None

                if transit_result and transit_result.routes:
                    for idx, route in enumerate(transit_result.routes):
                        route_type = RouteType.smart_combination

                        route_data = await RouteService.process_route_data(
                            route.model_dump(), TransportMode.bus, route_type
                        )
                        all_routes.append(route_data)

                if walking_result.routes:
                    route = walking_result.routes[0]
                    distance_km = route.distance

                    if distance_km <= 3.0:
                        route_data = await RouteService.process_route_data(
                            route.model_dump(),
                            TransportMode.walking,
                            RouteType.smart_combination,
                        )
                        all_routes.append(route_data)

                if not all_routes:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No suitable routes found between the specified locations",
                    )
                fastest_route = min(all_routes, key=lambda x: x.duration)
                fastest_route_data = RouteData(
                    type=RouteType.fastest.value,
                    mode=fastest_route.mode,
                    distance=fastest_route.distance,
                    duration=fastest_route.duration,
                    carbon=fastest_route.carbon,
                    route_details=fastest_route.route_details,
                    transit_info=fastest_route.transit_info,
                )

                # LOW_CARBON route: Only compare driving routes (car/motorbike)
                # This ensures it's always a driving mode, not transit or walking
                driving_routes = [r for r in all_routes if TransportMode.car in r.mode or TransportMode.motorbike in r.mode]
                if not driving_routes:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No driving routes found",
                    )
                
                lowest_carbon_route = min(driving_routes, key=lambda x: x.carbon)
                lowest_carbon_route_data = RouteData(
                    type=RouteType.low_carbon.value,
                    mode=lowest_carbon_route.mode,
                    distance=lowest_carbon_route.distance,
                    duration=lowest_carbon_route.duration,
                    carbon=lowest_carbon_route.carbon,
                    route_details=lowest_carbon_route.route_details,
                    transit_info=lowest_carbon_route.transit_info,
                )

                smart_route_data = RouteService.find_smart_route(
                    all_routes, fastest_route, max_time_ratio
                )

                routes_dict = {
                    RouteType.fastest: fastest_route_data,
                    RouteType.low_carbon: lowest_carbon_route_data,
                }

                if smart_route_data:
                    routes_dict[RouteType.smart_combination] = smart_route_data

                recommendation = await RouteService.generate_route_recommendation(
                    routes_dict, fastest_route, lowest_carbon_route
                )

            finally:
                if routes:
                    await routes.close()

            return FindRoutesResponse(
                origin=Location(
                    lat=origin.latitude, lng=origin.longitude
                ),
                destination=Location(
                    lat=destination.latitude, lng=destination.longitude
                ),
                routes=routes_dict,
                recommendation=recommendation.recommendation,
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to find optimal routes: {str(e)}",
            )

    @staticmethod
    def find_smart_route(
        all_routes: List[RouteData], fastest_route: RouteData, max_time_ratio: float
    ) -> Optional[RouteData]:
        """
        Find smart combination route that balances time and carbon emission.
        
        Priority:
        1. Transit route (if available and within acceptable time)
        2. Walking route (if distance <= 3km)
        3. Eco-optimized driving route (lowest carbon among driving alternatives)
        """
        try:
            max_acceptable_time = fastest_route.duration * max_time_ratio
            
            # Priority 1: Check for transit routes
            transit_routes = [r for r in all_routes if TransportMode.bus in r.mode]
            if transit_routes:
                best_transit = min(transit_routes, key=lambda x: x.carbon)
                
                driving_routes = [r for r in all_routes if TransportMode.car in r.mode]
                if driving_routes:
                    best_driving = min(driving_routes, key=lambda x: x.duration)
                    carbon_saving_percent = (
                        (
                            (best_driving.carbon - best_transit.carbon)
                            / best_driving.carbon
                            * 100
                        )
                        if best_driving.carbon > 0
                        else 0
                    )

                    if (
                        carbon_saving_percent > 30
                        or best_transit.duration <= max_acceptable_time
                    ):
                        return RouteData(
                            type=RouteType.smart_combination.value,
                            mode=best_transit.mode,
                            distance=best_transit.distance,
                            duration=best_transit.duration,
                            carbon=best_transit.carbon,
                            route_details=best_transit.route_details,
                            transit_info=best_transit.transit_info,
                        )

            # Priority 2: Check for walking routes (short distance)
            walking_routes = [r for r in all_routes if TransportMode.walking in r.mode]
            if walking_routes:
                walk_route = walking_routes[0]

                if (
                    walk_route.distance <= 3.0
                    and walk_route.duration <= max_acceptable_time
                ):
                    return RouteData(
                        type=RouteType.smart_combination.value,
                        mode=walk_route.mode,
                        distance=walk_route.distance,
                        duration=walk_route.duration,
                        carbon=walk_route.carbon,
                        route_details=walk_route.route_details,
                        transit_info=walk_route.transit_info,
                    )
            
            # Priority 3: When no transit available, select eco-optimized driving route
            # This is the "smart" choice when transit is not an option
            driving_routes = [r for r in all_routes if TransportMode.car in r.mode]
            if driving_routes:
                # Find driving route with best carbon/time balance
                # Prefer routes that are within acceptable time and have lower carbon
                eco_driving_candidates = [
                    r for r in driving_routes 
                    if r.duration <= max_acceptable_time
                ]
                
                if eco_driving_candidates:
                    # Among acceptable routes, pick the one with lowest carbon
                    best_eco_drive = min(eco_driving_candidates, key=lambda x: x.carbon)
                    
                    # Only return if it offers meaningful carbon savings vs fastest
                    if best_eco_drive.carbon < fastest_route.carbon * 0.9:  # At least 10% savings
                        return RouteData(
                            type=RouteType.smart_combination.value,
                            mode=best_eco_drive.mode,
                            distance=best_eco_drive.distance,
                            duration=best_eco_drive.duration,
                            carbon=best_eco_drive.carbon,
                            route_details=best_eco_drive.route_details,
                            transit_info=best_eco_drive.transit_info,
                        )

            return None
        except Exception as e:
            print(f"WARNING: Failed to find smart route - {str(e)}")
            return None

    @staticmethod
    async def generate_route_recommendation(
        routes: Dict[RouteType, RouteData],
        fastest_route: RouteData,
        lowest_carbon_route: RouteData,
    ) -> RecommendResponse:
        try:
            carbon_savings_vs_fastest = (
                fastest_route.carbon - lowest_carbon_route.carbon
            )
            carbon_savings_percent = (
                (carbon_savings_vs_fastest / fastest_route.carbon * 100)
                if fastest_route.carbon > 0
                else 0
            )

            time_difference = lowest_carbon_route.duration - fastest_route.duration
            distance_fastest = fastest_route.distance
            distance_lowest_carbon = lowest_carbon_route.distance

            route_info = []
            route_info.append(
                f"Fastest route: {fastest_route.mode[0].value}, "
                f"distance: {distance_fastest:.2f}km, "
                f"duration: {fastest_route.duration:.1f} minutes, "
                f"carbon: {fastest_route.carbon:.2f}kg CO2"
            )
            route_info.append(
                f"Lowest carbon route: {lowest_carbon_route.mode[0].value}, "
                f"distance: {distance_lowest_carbon:.2f}km, "
                f"duration: {lowest_carbon_route.duration:.1f} minutes, "
                f"carbon: {lowest_carbon_route.carbon:.2f}kg CO2"
            )

            if RouteType.smart_combination in routes:
                smart_route = routes[RouteType.smart_combination]
                route_info.append(
                    f"Smart combination route: {', '.join([m.value for m in smart_route.mode])}, "
                    f"distance: {smart_route.distance:.2f}km, "
                    f"duration: {smart_route.duration:.1f} minutes, "
                    f"carbon: {smart_route.carbon:.2f}kg CO2"
                )

            prompt = f"""You are a sustainable transportation advisor. Analyze these route options and provide a brief, friendly recommendation (max 2 sentences) for which route to choose and why.

Route options:
{chr(10).join(route_info)}

Key insights:
- Carbon savings: {carbon_savings_percent:.1f}% when choosing lowest carbon vs fastest
- Time difference: {abs(time_difference):.1f} minutes {"slower" if time_difference > 0 else "faster"}

Provide a concise recommendation that balances environmental impact and convenience. Focus on the most practical choice for the user."""

            text_gen = await create_text_generator_api()
            ai_recommendation = await text_gen.generate_reply(
                [{"role": "user", "content": prompt}]
            )

            recommended_route = "fastest"
            if (
                carbon_savings_percent > 50
                and lowest_carbon_route.duration <= fastest_route.duration * 1.5
            ):
                recommended_route = "lowest_carbon"
            elif (
                RouteType.smart_combination in routes
                and routes[RouteType.smart_combination].carbon
                < fastest_route.carbon * 0.7
            ):
                recommended_route = "smart_combination"

            return RecommendResponse(
                route=recommended_route, recommendation=ai_recommendation.strip()
            )
        except Exception as e:
            print(f"WARNING: Failed to generate AI recommendation - {str(e)}")

            carbon_savings_percent = (
                (
                    (fastest_route.carbon - lowest_carbon_route.carbon)
                    / fastest_route.carbon
                    * 100
                )
                if fastest_route.carbon > 0
                else 0
            )

            if carbon_savings_percent > 50:
                return RecommendResponse(
                    route="lowest_carbon",
                    recommendation=f"Saves {carbon_savings_percent:.1f}% carbon emissions with only {abs(lowest_carbon_route.duration - fastest_route.duration):.1f} minutes difference",
                )
            return RecommendResponse(
                route="fastest", recommendation="Optimal balance of time and efficiency"
            )

    @staticmethod
    def _haversine_distance(
        lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        R = 6371  # Earth radius (km)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(
            math.radians(lat1)
        ) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        return distance

    @staticmethod
    async def calculate_trip_metrics(
        destinations: List[PlanDestination],
    ) -> TripMetricsResponse:
        if len(destinations) < 2:
            return TripMetricsResponse(
                total_distance_km=0.0, total_duration_min=0.0, details=[]
            )

        sorted_dests = sorted(destinations, key=lambda x: x.order_in_day)

        total_distance = 0
        total_duration = 0
        route_details = []

        # Conversion factor from straight-line to road distance (road is typically 1.3-1.5x longer)
        ROAD_FACTOR = 1.4
        # Average speed in city (km/h) - used for time calculation
        AVG_SPEED_KMH = 30

        for i in range(len(sorted_dests) - 1):
            start_node = sorted_dests[i]
            end_node = sorted_dests[i + 1]

            start_coords = await MapService.get_coordinates(start_node.destination_id)
            end_coords = await MapService.get_coordinates(end_node.destination_id)

            if not start_coords or not end_coords:
                continue

            air_distance = RouteService._haversine_distance(
                start_coords.latitude,
                start_coords.longitude,
                end_coords.latitude,
                end_coords.longitude,
            )

            estimated_km = air_distance * ROAD_FACTOR
            estimated_min = (estimated_km / AVG_SPEED_KMH) * 60

            # If distance is very short (<1km), assume walking speed
            if estimated_km < 1.0:
                estimated_min = (estimated_km / 5) * 60  # Walking speed: 5km/h

            total_distance += estimated_km
            total_duration += estimated_min

            route_details.append(
                {
                    "from": start_node.destination_id,
                    "to": end_node.destination_id,
                    "km": round(estimated_km, 2),
                    "min": round(estimated_min, 0),
                }
            )

        return TripMetricsResponse(
            total_distance_km=round(total_distance, 2),
            total_duration_min=round(total_duration, 0),
            details=route_details,
        )

    @staticmethod
    async def get_route_for_plan(
        origin: str, destination: str, transport_mode: TransportMode = TransportMode.car
) -> List[RouteForPlanResponse]:
        try:
            origin_coords = await MapService.get_coordinates(place_id=origin)
            destination_coords = await MapService.get_coordinates(place_id=destination)

            if not origin_coords or not destination_coords:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not retrieve coordinates for origin or destination",
                )

            result = await RouteService.find_three_optimal_routes(
                FindRoutesRequest(origin=origin_coords, destination=destination_coords),
            )

            if not result.routes:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No route found between the specified locations",
                )

            list_response = []
            for route_type, route_data in result.routes.items():
                # Filter by transport_mode if specified and not default
                if transport_mode != TransportMode.car and transport_mode not in route_data.mode:
                    continue

                # Extract polyline from the Route object stored in route_details dict
                polyline = ""
                if isinstance(route_data.route_details, dict) and "overview_polyline" in route_data.route_details:
                    polyline = route_data.route_details["overview_polyline"]
                elif hasattr(route_data.route_details, "overview_polyline"):
                    polyline = route_data.route_details.overview_polyline

                list_response.append(
                    RouteForPlanResponse(
                        origin=origin,
                        destination=destination,
                        distance_km=route_data.distance,
                        estimated_travel_time_min=route_data.duration,
                        carbon_emission_kg=route_data.carbon,
                        route_polyline=polyline,
                        transport_mode=route_data.mode[0] if route_data.mode else transport_mode,
                        route_type=route_type,
                    )
                )
            return list_response
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get route for plan: {str(e)}",
            )