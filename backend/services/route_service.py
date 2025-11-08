from fastapi import HTTPException, status
from typing import Any, List, Dict, Optional
from services.map_service import create_maps_client
from schemas.route_schema import *

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
                if step.get("travel_mode") == "TRANSIT":
                    transit_details = step.get("transit_details", {})
                    transit_steps.append({
                        "line": transit_details.get("line", {}).get("short_name", "N/A"),
                        "vehicle": transit_details.get("line", {}).get("vehicle", {}).get("type", "BUS"),
                        "departure_stop": transit_details.get("departure_stop", {}).get("name", ""),
                        "arrival_stop": transit_details.get("arrival_stop", {}).get("name", ""),
                        "num_stops": transit_details.get("num_stops", 0),
                        "duration": step.get("duration", {}).get("text", "")
                    })
                elif step.get("travel_mode") == "WALKING":
                    walking_steps.append({
                        "distance": step.get("distance", {}).get("text", ""),
                        "duration": step.get("duration", {}).get("text", ""),
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
    async def calculate_route_carbon(
        distance_km: float, 
        mode: TransportMode,
        fuel_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """        
        Args:
            distance_km: Distance in kilometers
            mode: Transport mode
            fuel_type: Fuel type (default: petrol)
            congestion_ratio: Traffic congestion (duration_in_traffic / duration_normal)
        """
        try:
            if distance_km < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Distance cannot be negative"
                )
            
            result = await CarbonService.calculate_emission_by_mode(
                distance_km, 
                mode,
                fuel_type=fuel_type
            )
            
            return {
                "co2": result.total_co2_kg,
                "distance_km": result.distance_km,
                "mode": mode,
                "fuel_type": result.fuel_type,
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to calculate route carbon: {str(e)}"
            )

    @staticmethod
    async def process_route_data(
        route: Dict[str, Any],
        mode: str,
        route_type: str,
        display_name: str
    ) -> Dict[str, Any]:
        """Process route data and calculate carbon emissions"""
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
            
            # Calculate traffic congestion ratio if available
            congestion_ratio = 1.0
            has_traffic_data = False
            
            if "duration_in_traffic" in leg:
                duration_in_traffic = leg["duration_in_traffic"]["value"]
                duration_normal = leg["duration"]["value"]
                
                if duration_normal > 0:
                    congestion_ratio = duration_in_traffic / duration_normal
                    has_traffic_data = True
            
            # Calculate carbon with traffic consideration
            carbon_data = await RouteService.calculate_route_carbon(
                distance_km, 
                mode,
                congestion_ratio=congestion_ratio
            )
            
            result = {
                "type": route_type,
                "mode": mode,
                "display_name": display_name,
                "distance_km": distance_km,
                "duration_min": duration_min,
                "duration_text": leg["duration"]["text"],
                "carbon_kg": carbon_data["co2_kg"],
                "carbon_grams": carbon_data["co2_grams"],
                "emission_factor": carbon_data["emission_factor_g_per_km"],
                "route_details": route,
                "priority_score": duration_min,
                "has_traffic_data": has_traffic_data
            }
            
            # Add traffic info if available
            if has_traffic_data:
                result["traffic_info"] = {
                    "congestion_ratio": round(congestion_ratio, 2),
                    "duration_in_traffic_min": round(duration_in_traffic / 60, 1),
                    "traffic_delay_min": round((duration_in_traffic - duration_normal) / 60, 1),
                    "traffic_multiplier": carbon_data.get("traffic_multiplier"),
                    "emission_increase_percent": carbon_data.get("emission_increase_percent")
                }
            
            if mode == "transit":
                result["transit_info"] = RouteService.extract_transit_details(leg)
            
            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process route data: {str(e)}"
            )
    
    @staticmethod
    async def find_three_optimal_routes(
        origin: str,
        destination: str,
        max_time_ratio: float = 1.3,
        language: str = "vi"
    ) -> Dict[str, Any]:
        """Find 3 optimal routes: fastest, lowest carbon, and smart combination"""
        try:
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
            
            results = {
                "origin": origin,
                "destination": destination,
                "routes": {},
                "recommendation": None
            }
            
            maps = await create_maps_client()
            
            try:
                # Get driving routes with traffic data (departure_time="now")
                driving_result = await maps.get_route_with_traffic(
                    origin, destination, mode="driving", departure_time="now"
                )
                
                # Get additional driving alternatives (without traffic for comparison)
                driving_alternatives = await maps.get_directions(
                    origin, destination, mode="driving", alternatives=True, language=language
                )
                
                transit_result = await maps.get_directions(origin, destination, mode="transit", alternatives=True, language=language)
                walking_result = await maps.get_directions(origin, destination, mode="walking", language=language)
                bicycling_result = await maps.get_directions(origin, destination, mode="bicycling", language=language)
                
                all_routes = []
                
                # Process driving route with traffic data
                if driving_result.get("status") == "OK" and driving_result.get("route"):
                    route = driving_result["route"]
                    display_name = "Driving (with traffic)"
                    route_type = "fastest_driving"
                    
                    route_data = await RouteService.process_route_data(
                        route, "driving", route_type, display_name
                    )
                    all_routes.append(route_data)
                
                # Process alternative driving routes (if any)
                if driving_alternatives.get("status") == "OK" and driving_alternatives.get("routes"):
                    for idx, route in enumerate(driving_alternatives["routes"][1:], start=1):
                        display_name = f"Driving (option {idx+1})"
                        route_type = f"alternative_driving_{idx}"
                        
                        route_data = await RouteService.process_route_data(
                            route, "driving", route_type, display_name
                        )
                        all_routes.append(route_data)
                
                if transit_result.get("status") == "OK" and transit_result.get("routes"):
                    for idx, route in enumerate(transit_result["routes"]):
                        display_name = "Public transport"
                        route_type = "transit" if idx == 0 else f"alternative_transit_{idx}"
                        
                        route_data = await RouteService.process_route_data(
                            route, "transit", route_type, display_name
                        )
                        all_routes.append(route_data)
                
                if walking_result.get("status") == "OK" and walking_result.get("routes"):
                    route = walking_result["routes"][0]
                    leg = route["legs"][0]
                    distance_km = leg["distance"]["value"] / 1000
                    
                    if distance_km <= 3.0:
                        route_data = await RouteService.process_route_data(
                            route, "walking", "walking", "Walking"
                        )
                        all_routes.append(route_data)
                
                if bicycling_result.get("status") == "OK" and bicycling_result.get("routes"):
                    route = bicycling_result["routes"][0]
                    route_data = await RouteService.process_route_data(
                        route, "bicycling", "bicycling", "Bicycling"
                    )
                    all_routes.append(route_data)
                
                if not all_routes:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No suitable routes found between the specified locations"
                    )
                
                fastest_route = min(all_routes, key=lambda x: x["duration_min"])
                results["routes"]["fastest"] = {
                    **fastest_route,
                    "reason": "Fastest route"
                }
                
                lowest_carbon_route = min(all_routes, key=lambda x: x["carbon_kg"])
                results["routes"]["lowest_carbon"] = {
                    **lowest_carbon_route,
                    "reason": "Lowest carbon emissions"
                }
                
                smart_route = RouteService._find_smart_route(
                    all_routes, fastest_route, max_time_ratio
                )
                
                if smart_route:
                    results["routes"]["smart_combination"] = smart_route
                
                results["recommendation"] = RouteService._generate_recommendation(
                    results["routes"], fastest_route, lowest_carbon_route
                )
                
                results["status"] = "OK"
                results["total_routes_analyzed"] = len(all_routes)
                
            finally:
                await maps.close()
            
            return results
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to find optimal routes: {str(e)}"
            )
    
    @staticmethod
    def find_smart_route(
        all_routes: List[Dict[str, Any]],
        fastest_route: Dict[str, Any],
        max_time_ratio: float
    ) -> Optional[Dict[str, Any]]:
        """Find smart route prioritizing transit, walking, or bicycling"""
        try:
            transit_routes = [r for r in all_routes if r["mode"] == "transit"]
            
            if transit_routes:
                best_transit = min(transit_routes, key=lambda x: x["carbon_kg"])
                
                driving_routes = [r for r in all_routes if r["mode"] == "driving"]
                if driving_routes:
                    best_driving = min(driving_routes, key=lambda x: x["duration_min"])
                    carbon_saving_percent = (
                        (best_driving["carbon_kg"] - best_transit["carbon_kg"]) 
                        / best_driving["carbon_kg"] * 100
                    ) if best_driving["carbon_kg"] > 0 else 0
                    
                    max_acceptable_time = fastest_route["duration_min"] * max_time_ratio
                    
                    if carbon_saving_percent > 30 or best_transit["duration_min"] <= max_acceptable_time:
                        return {
                            **best_transit,
                            "reason": f"Smart route (walking + public transport, saves {carbon_saving_percent:.1f}% carbon)",
                            "time_comparison": {
                                "vs_fastest_min": round(best_transit["duration_min"] - fastest_route["duration_min"], 1),
                                "vs_fastest_percent": round((best_transit["duration_min"] / fastest_route["duration_min"] - 1) * 100, 1)
                            },
                            "carbon_comparison": {
                                "vs_driving_kg": round(best_driving["carbon_kg"] - best_transit["carbon_kg"], 3),
                                "vs_driving_percent": round(carbon_saving_percent, 1)
                            }
                        }
            
            walking_routes = [r for r in all_routes if r["mode"] == "walking"]
            if walking_routes:
                walk_route = walking_routes[0]
                max_acceptable_time = fastest_route["duration_min"] * max_time_ratio
                
                if walk_route["distance_km"] <= 3.0 and walk_route["duration_min"] <= max_acceptable_time:
                    return {
                        **walk_route,
                        "reason": "Smart route (walking - short distance, zero carbon)",
                        "time_comparison": {
                            "vs_fastest_min": round(walk_route["duration_min"] - fastest_route["duration_min"], 1),
                            "vs_fastest_percent": round((walk_route["duration_min"] / fastest_route["duration_min"] - 1) * 100, 1)
                        }
                    }
            
            bicycling_routes = [r for r in all_routes if r["mode"] == "bicycling"]
            if bicycling_routes:
                bike_route = bicycling_routes[0]
                max_acceptable_time = fastest_route["duration_min"] * max_time_ratio
                
                if bike_route["duration_min"] <= max_acceptable_time:
                    return {
                        **bike_route,
                        "reason": "Smart route (bicycling - zero carbon)",
                        "time_comparison": {
                            "vs_fastest_min": round(bike_route["duration_min"] - fastest_route["duration_min"], 1),
                            "vs_fastest_percent": round((bike_route["duration_min"] / fastest_route["duration_min"] - 1) * 100, 1)
                        }
                    }
            
            return None
        except Exception as e:
            # Don't raise exception for smart route finding, just return None
            print(f"Warning: Failed to find smart route: {str(e)}")
            return None
        
    @staticmethod
    def generate_route_recommendation(
        routes: Dict[str, Any],
        fastest_route: Dict[str, Any],
        lowest_carbon_route: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate route recommendation based on carbon savings and time trade-offs"""
        try:
            carbon_savings_vs_fastest = fastest_route["carbon_kg"] - lowest_carbon_route["carbon_kg"]
            carbon_savings_percent = (
                carbon_savings_vs_fastest / fastest_route["carbon_kg"] * 100
            ) if fastest_route["carbon_kg"] > 0 else 0
            
            recommendation = {
                "route": "fastest",
                "reason": "Maximum time savings"
            }
            
            if carbon_savings_percent > 50 and lowest_carbon_route["duration_min"] <= fastest_route["duration_min"] * 1.5:
                recommendation = {
                    "route": "lowest_carbon",
                    "reason": f"Saves {carbon_savings_percent:.1f}% carbon, only {lowest_carbon_route['duration_min'] - fastest_route['duration_min']:.1f} min slower"
                }
            elif "smart_combination" in routes and routes["smart_combination"]["carbon_kg"] < fastest_route["carbon_kg"] * 0.7:
                recommendation = {
                    "route": "smart_combination",
                    "reason": "Good balance between time and carbon"
                }
            
            return recommendation
        except Exception as e:
            # Fallback recommendation if generation fails
            print(f"Warning: Failed to generate recommendation: {str(e)}")
            return {
                "route": "fastest",
                "reason": "Default recommendation"
            }