from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from schemas.route_schema import *
from schemas.map_schema import DirectionsRequest
from services.carbon_service import CarbonService
from integration.route_api import create_route_api_client
from integration.text_generator_api import get_text_generator

class RouteService:
    @staticmethod
    def extract_transit_details(leg: Dict[str, Any]) -> TransitDetails:
        try:
            if not leg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Leg data is required"
                )
            
            transit_steps = []
            walking_steps = []
            
            for step in leg.get("steps", []):
                if step.get("travel_mode") == "TRANSIT":
                    transit_details = step.get("transit_details", {})
                    departure_stop = transit_details.get("departure_stop", {})
                    arrival_stop = transit_details.get("arrival_stop", {})
                    
                    transit_steps.append({
                        "line": transit_details.get("line", {}).get("short_name", "N/A"),
                        "vehicle": TransportMode.bus,
                        "departure_stop": {
                            "lat": departure_stop.get("location", {}).get("lat", 0.0),
                            "lng": departure_stop.get("location", {}).get("lng", 0.0)
                        },
                        "arrival_stop": {
                            "lat": arrival_stop.get("location", {}).get("lat", 0.0),
                            "lng": arrival_stop.get("location", {}).get("lng", 0.0)
                        },
                        "num_stops": transit_details.get("num_stops", 0),
                        "duration": step.get("duration", {}).get("value", 0) / 60
                    })
                elif step.get("travel_mode") == "WALKING":
                    walking_steps.append({
                        "distance": step.get("distance", {}).get("value", 0),
                        "duration": step.get("duration", {}).get("value", 0) / 60,
                        "instruction": step.get("html_instructions", "")
                    })
            
            return TransitDetails(
                transit_steps=[TransitStep(**step) for step in transit_steps],
                walking_steps=[WalkingStep(**step) for step in walking_steps],
                total_transit_steps=len(transit_steps),
                total_walking_steps=len(walking_steps)
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to extract transit details: {str(e)}"
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
                    detail="Invalid route data: missing legs information"
                )
            
            leg = route["legs"][0]
            distance_km = leg["distance"]
            duration_min = leg["duration"]

            carbon_response = await CarbonService.estimate_transport_emission(mode, distance_km)

            result = RouteData(
                type=route_type,
                mode=[mode],
                distance=distance_km,
                duration=duration_min,
                carbon=carbon_response,
                route_details=route
            )

            if mode == TransportMode.bus:
                result.transit_info = RouteService.extract_transit_details(leg)

            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process route data: {str(e)}"
            )
    
    @staticmethod
    async def find_three_optimal_routes(request: FindRoutesRequest) -> FindRoutesResponse:
        try:
            origin = request.origin
            destination = request.destination
            max_time_ratio = request.max_time_ratio
            language = request.language
            
            if not origin or not destination:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Origin and destination are required"
                )
            
            if max_time_ratio <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="max_time_ratio must be greater than 0"
                )
            
            routes_dict = {}
            
            try:
                routes = await create_route_api_client()
                
                driving_alternatives = await routes.get_routes(
                    data=DirectionsRequest(origin=origin, destination=destination, alternatives=True),
                    mode=TransportMode.car,
                    language=language
                )

                transit_result = await routes.get_routes(
                    data=DirectionsRequest(origin=origin, destination=destination, alternatives=True),
                    mode=TransportMode.bus,
                    language=language
                )
                
                walking_result = await routes.get_routes(
                    data=DirectionsRequest(origin=origin, destination=destination),
                    mode=TransportMode.walking,
                    language=language
                )
                
                all_routes = []

                if driving_alternatives.routes:
                    for idx, route in enumerate(driving_alternatives.routes):
                        # first driving route is treated as the fastest candidate
                        route_type = RouteType.fastest if idx == 0 else RouteType.fastest

                        route_data = await RouteService.process_route_data(
                            route.model_dump(), TransportMode.car, route_type
                        )
                        all_routes.append(route_data)

                try:
                    eco_result = await routes.get_eco_friendly_route(
                        data=DirectionsRequest(origin=origin, destination=destination, alternatives=True),
                        mode=TransportMode.car,
                        vehicle_type="GASOLINE",
                        language=language
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
                            route.model_dump(), TransportMode.walking, RouteType.smart_combination
                        )
                        all_routes.append(route_data)

                if not all_routes:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No suitable routes found between the specified locations"
                    )
                fastest_route = min(all_routes, key=lambda x: x.duration)
                fastest_route_data = RouteData(
                    type=RouteType.fastest.value,
                    mode=fastest_route.mode,
                    distance=fastest_route.distance,
                    duration=fastest_route.duration,
                    carbon=fastest_route.carbon,
                    route_details=fastest_route.route_details,
                    transit_info=fastest_route.transit_info
                )
                
                lowest_carbon_route = min(all_routes, key=lambda x: x.carbon)
                lowest_carbon_route_data = RouteData(
                    type=RouteType.low_carbon.value,
                    mode=lowest_carbon_route.mode,
                    distance=lowest_carbon_route.distance,
                    duration=lowest_carbon_route.duration,
                    carbon=lowest_carbon_route.carbon,
                    route_details=lowest_carbon_route.route_details,
                    transit_info=lowest_carbon_route.transit_info
                )
                
                smart_route_data = RouteService.find_smart_route(
                    all_routes, fastest_route, max_time_ratio
                )
                
                routes_dict = {
                    RouteType.fastest: fastest_route_data,
                    RouteType.low_carbon: lowest_carbon_route_data
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
                origin={"lat": origin[0], "lng": origin[1]},
                destination={"lat": destination[0], "lng": destination[1]},
                routes=routes_dict,
                recommendation=recommendation.recommendation
            )
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to find optimal routes: {str(e)}"
            )
    
    @staticmethod
    def find_smart_route(
        all_routes: List[RouteData],
        fastest_route: RouteData,
        max_time_ratio: float
    ) -> Optional[RouteData]:
        try:
            transit_routes = [r for r in all_routes if TransportMode.bus in r.mode]
            
            if transit_routes:
                best_transit = min(transit_routes, key=lambda x: x.carbon)
                
                driving_routes = [r for r in all_routes if TransportMode.car in r.mode]
                if driving_routes:
                    best_driving = min(driving_routes, key=lambda x: x.duration)
                    carbon_saving_percent = (
                        (best_driving.carbon - best_transit.carbon) 
                        / best_driving.carbon * 100
                    ) if best_driving.carbon > 0 else 0
                    
                    max_acceptable_time = fastest_route.duration * max_time_ratio
                    
                    if carbon_saving_percent > 30 or best_transit.duration <= max_acceptable_time:
                        return RouteData(
                            type=RouteType.smart_combination.value,
                            mode=best_transit.mode,
                            distance=best_transit.distance,
                            duration=best_transit.duration,
                            carbon=best_transit.carbon,
                            route_details=best_transit.route_details,
                        transit_info=best_transit.transit_info
                    )
            
            walking_routes = [r for r in all_routes if TransportMode.walking in r.mode]
            if walking_routes:
                walk_route = walking_routes[0]
                max_acceptable_time = fastest_route.duration * max_time_ratio
                
                if walk_route.distance <= 3.0 and walk_route.duration <= max_acceptable_time:
                    return RouteData(
                        type=RouteType.smart_combination.value,
                        mode=walk_route.mode,
                        distance=walk_route.distance,
                        duration=walk_route.duration,
                        carbon=walk_route.carbon,
                        route_details=walk_route.route_details,
                        transit_info=walk_route.transit_info
                    )
                                
            return None
        except Exception as e:
            print(f"WARNING: Failed to find smart route - {str(e)}")
            return None
        
    @staticmethod
    async def generate_route_recommendation(
        routes: Dict[RouteType, RouteData],
        fastest_route: RouteData,
        lowest_carbon_route: RouteData
    ) -> RecommendResponse:
        try:
            carbon_savings_vs_fastest = fastest_route.carbon - lowest_carbon_route.carbon
            carbon_savings_percent = (
                carbon_savings_vs_fastest / fastest_route.carbon * 100
            ) if fastest_route.carbon > 0 else 0
            
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
- Time difference: {abs(time_difference):.1f} minutes {'slower' if time_difference > 0 else 'faster'}

Provide a concise recommendation that balances environmental impact and convenience. Focus on the most practical choice for the user."""

            text_gen = get_text_generator()
            ai_recommendation = await text_gen.generate_text(prompt)
            
            recommended_route = "fastest"
            if carbon_savings_percent > 50 and lowest_carbon_route.duration <= fastest_route.duration * 1.5:
                recommended_route = "lowest_carbon"
            elif RouteType.smart_combination in routes and routes[RouteType.smart_combination].carbon < fastest_route.carbon * 0.7:
                recommended_route = "smart_combination"
            
            return RecommendResponse(
                route=recommended_route,
                recommendation=ai_recommendation.strip()
            )
        except Exception as e:
            print(f"WARNING: Failed to generate AI recommendation - {str(e)}")
            
            carbon_savings_percent = (
                (fastest_route.carbon - lowest_carbon_route.carbon) / fastest_route.carbon * 100
            ) if fastest_route.carbon > 0 else 0
            
            if carbon_savings_percent > 50:
                return RecommendResponse(
                    route="lowest_carbon",
                    recommendation=f"Saves {carbon_savings_percent:.1f}% carbon emissions with only {abs(lowest_carbon_route.duration - fastest_route.duration):.1f} minutes difference"
                )
            return RecommendResponse(
                route="fastest",
                recommendation="Optimal balance of time and efficiency"
            )