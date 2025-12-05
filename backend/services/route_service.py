from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from schemas.map_schema import Location
from integration.route_api import create_route_api_client
from integration.text_generator_api import create_text_generator_api
from services.map_service import MapService
from schemas.route_schema import (
    DirectionsRequest,
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
        try:
            if not leg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Leg data is required",
                )

            transit_steps = []
            walking_steps = []

            for step in leg.get("steps", []):
                if step.get("travel_mode") == "TRANSIT":
                    transit_details = step.get("transit_details", {})
                    departure_stop = transit_details.get("departure_stop", {})
                    arrival_stop = transit_details.get("arrival_stop", {})

                    transit_steps.append(
                        {
                            "line": (
                                transit_details.get("line", {}).get("short_name", "N/A")
                            ),
                            "vehicle": TransportMode.bus,
                            "departure_stop": {
                                "lat": (
                                    departure_stop.get("location", {}).get("lat", 0.0)
                                ),
                                "lng": (
                                    departure_stop.get("location", {}).get("lng", 0.0)
                                ),
                            },
                            "arrival_stop": {
                                "lat": arrival_stop.get("location", {}).get("lat", 0.0),
                                "lng": arrival_stop.get("location", {}).get("lng", 0.0),
                            },
                            "num_stops": transit_details.get("num_stops", 0),
                            "duration": step.get("duration", {}).get("value", 0) / 60,
                        }
                    )
                elif step.get("travel_mode") == "WALKING":
                    walking_steps.append(
                        {
                            "distance": step.get("distance", {}).get("value", 0),
                            "duration": step.get("duration", {}).get("value", 0) / 60,
                            "instruction": step.get("html_instructions", ""),
                        }
                    )

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

            if mode == TransportMode.bus:
                result.transit_info = RouteService.extract_transit_details(leg)

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

                transit_result = await routes.get_routes(
                    data=DirectionsRequest(
                        origin=origin, destination=destination, alternatives=True
                    ),
                    mode=TransportMode.bus,
                    language=language,
                )

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

                try:
                    eco_result = await routes.get_eco_friendly_route(
                        data=DirectionsRequest(
                            origin=origin, destination=destination, alternatives=True
                        ),
                        mode=TransportMode.car,
                        vehicle_type="GASOLINE",
                        language=language,
                    )
                except Exception:
                    eco_result = None

                if eco_result and eco_result.routes:
                    eco_route = eco_result.routes[0]
                    eco_route_data = await RouteService.process_route_data(
                        eco_route.model_dump(), TransportMode.car, RouteType.low_carbon
                    )
                    all_routes.append(eco_route_data)

                if transit_result.routes:
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

                lowest_carbon_route = min(all_routes, key=lambda x: x.carbon)
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
        try:
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

                    max_acceptable_time = fastest_route.duration * max_time_ratio

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

            walking_routes = [r for r in all_routes if TransportMode.walking in r.mode]
            if walking_routes:
                walk_route = walking_routes[0]
                max_acceptable_time = fastest_route.duration * max_time_ratio

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
                start_coords["lat"],
                start_coords["lng"],
                end_coords["lat"],
                end_coords["lng"],
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
                list_response.append(
                    RouteForPlanResponse(
                        origin=origin,
                        destination=destination,
                        distance_km=route_data.distance,
                        estimated_travel_time_min=route_data.duration,
                        carbon_emission_kg=route_data.carbon,
                        route_polyline=route_data.route_details.get(
                            "overview_polyline", ""
                        ),
                        transport_mode=transport_mode,
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