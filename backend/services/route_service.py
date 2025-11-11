from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from models.route import RouteType
from schemas.route_schema import *
from services.carbon_service import CarbonService
from services.map_service import create_maps_client

class RouteService:
    @staticmethod
    def extract_transit_details(leg: Dict[str, Any]) -> TransitDetails:
        """Extract transit step details from Google Maps leg data"""
        try:
            if not leg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Leg data is required"
                )
            
            transit_steps = []
            walking_steps = []
            
            for step in leg.get("steps", []):
                if step.get("travel_mode") == "bus":
                    transit_details = step.get("transit_details", {})
                    departure_stop = transit_details.get("departure_stop", {})
                    arrival_stop = transit_details.get("arrival_stop", {})
                    
                    transit_steps.append({
                        "line": transit_details.get("line", {}).get("short_name", "N/A"),
                        "vehicle": TransportMode.transit,
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
                elif step.get("travel_mode") == "walking":
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
            
            if "distance" not in leg or "value" not in leg["distance"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid route data: missing distance information"
                )
            
            if "duration" not in leg or "value" not in leg["duration"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid route data: missing duration information"
                )
            
            distance_km = leg["distance"]["value"] / 1000
            duration_min = leg["duration"]["value"] / 60

            carbon_response = await CarbonService.estimate_transport_emission(mode, distance_km)

            result = RouteData(
                type=route_type,
                mode=mode,
                distance=distance_km,
                duration=duration_min,
                carbon=carbon_response,
                route_details=route
            )

            if mode == TransportMode.bus:
                result.transit_info = RouteService.extract_transit_details(leg)

            return result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process route data: {str(e)}"
            )
    
    @staticmethod
    async def find_three_optimal_routes(request: FindRoutesRequest) -> FindRoutesResponse:
        """Find 3 optimal routes: fastest, lowest carbon, and smart combination"""
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
            
            maps = await create_maps_client()
            
            try:
                driving_result = await maps.get_route(origin, destination)

                driving_alternatives = await maps.get_directions(
                    origin, destination, mode=TransportMode.car, alternatives=True, language=language
                )

                transit_result = await maps.get_directions(origin, destination, mode=TransportMode.bus, alternatives=True, language=language)
                walking_result = await maps.get_directions(origin, destination, mode=TransportMode.walking, language=language)
                cycling_result = await maps.get_directions(origin, destination, mode=TransportMode.cycling, language=language)

                all_routes = []
                
                # Process driving route (Pydantic response)
                if driving_result.status == "OK" and driving_result.routes:
                    route = driving_result.routes[0]
                    route_type = RouteType.fastest
                    
                    route_data = await RouteService.process_route_data(
                        route.model_dump(), TransportMode.car, route_type
                    )
                    all_routes.append(route_data)
                
                # Process alternative driving routes
                if driving_alternatives.status == "OK" and driving_alternatives.routes:
                    for idx, route in enumerate(driving_alternatives.routes[1:], start=1):
                        route_type = RouteType.low_carbon
                        
                        route_data = await RouteService.process_route_data(
                            route.model_dump(), TransportMode.car, route_type
                        )
                        all_routes.append(route_data)
                
                # Process transit routes
                if transit_result.status == "OK" and transit_result.routes:
                    for idx, route in enumerate(transit_result.routes):
                        route_type = RouteType.smart_combination
                        
                        route_data = await RouteService.process_route_data(
                            route.model_dump(), TransportMode.bus, route_type
                        )
                        all_routes.append(route_data)
                
                # Process walking route
                if walking_result.status == "OK" and walking_result.routes:
                    route = walking_result.routes[0]
                    leg = route.legs[0]
                    distance_km = leg.distance.value / 1000
                    
                    if distance_km <= 3.0:
                        route_data = await RouteService.process_route_data(
                            route.model_dump(), TransportMode.walking, RouteType.smart_combination
                        )
                        all_routes.append(route_data)

                # Process cycling route
                if cycling_result.status == "OK" and cycling_result.routes:
                    route = cycling_result.routes[0]
                    route_data = await RouteService.process_route_data(
                        route.model_dump(), TransportMode.cycling, RouteType.smart_combination
                    )
                    all_routes.append(route_data)
                
                if not all_routes:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No suitable routes found between the specified locations"
                    )
                
                # Find fastest route
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
                
                # Find lowest carbon route
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
                
                # Find smart combination route
                smart_route_data = RouteService.find_smart_route(
                    all_routes, fastest_route, max_time_ratio
                )
                
                # Build routes dict
                routes_dict = {
                    RouteType.fastest: fastest_route_data,
                    RouteType.low_carbon: lowest_carbon_route_data
                }
                
                if smart_route_data:
                    routes_dict[RouteType.smart_combination] = smart_route_data
                
                # Generate recommendation
                recommendation = RouteService.generate_route_recommendation(
                    routes_dict, fastest_route, lowest_carbon_route
                )
                
            finally:
                await maps.close()
            
            return FindRoutesResponse(
                origin={"lat": origin[0], "lng": origin[1]},
                destination={"lat": destination[0], "lng": destination[1]},
                routes=routes_dict,
                recommendation=recommendation["reason"]
            )
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
        """Find smart route prioritizing transit, walking, or bicycling"""
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

            cycling_routes = [r for r in all_routes if TransportMode.cycling in r.mode]
            if cycling_routes:
                bike_route = cycling_routes[0]
                max_acceptable_time = fastest_route.duration * max_time_ratio
                
                if bike_route.duration <= max_acceptable_time:
                    return RouteData(
                        type=RouteType.smart_combination.value,
                        mode=bike_route.mode,
                        distance=bike_route.distance,
                        duration=bike_route.duration,
                        carbon=bike_route.carbon,
                        route_details=bike_route.route_details,
                        transit_info=bike_route.transit_info
                    )
            
            return None
        except Exception as e:
            print(f"WARNING: Failed to find smart route - {str(e)}")
            return None
        
    @staticmethod
    def generate_route_recommendation(
        routes: Dict[RouteType, RouteData],
        fastest_route: RouteData,
        lowest_carbon_route: RouteData
    ) -> Dict[str, str]:
        """Generate route recommendation based on carbon savings and time trade-offs"""
        try:
            carbon_savings_vs_fastest = fastest_route.carbon - lowest_carbon_route.carbon
            carbon_savings_percent = (
                carbon_savings_vs_fastest / fastest_route.carbon * 100
            ) if fastest_route.carbon > 0 else 0
            
            recommendation = {
                "route": "fastest",
                "reason": "Maximum time savings"
            }
            
            if carbon_savings_percent > 50 and lowest_carbon_route.duration <= fastest_route.duration * 1.5:
                recommendation = {
                    "route": "lowest_carbon",
                    "reason": f"Saves {carbon_savings_percent:.1f}% carbon, only {lowest_carbon_route.duration - fastest_route.duration:.1f} min slower"
                }
            elif RouteType.smart_combination in routes and routes[RouteType.smart_combination].carbon < fastest_route.carbon * 0.7:
                recommendation = {
                    "route": "smart_combination",
                    "reason": "Good balance between time and carbon"
                }
            
            return recommendation
        except Exception as e:
            print(f"WARNING: Failed to generate recommendation - {str(e)}")
            return {
                "route": "fastest",
                "reason": "Default recommendation"
            }
