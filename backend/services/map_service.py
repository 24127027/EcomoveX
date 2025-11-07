from typing import Dict, List, Optional, Any
from integration.google_map_api import GoogleMapsAPI, create_maps_client
from services.carbon_service import CarbonService
from fastapi import HTTPException, status

class MapService:
    @staticmethod
    async def calculate_route_carbon(distance_km: float, mode: str) -> Dict[str, Any]:
        try:
            if distance_km < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Distance cannot be negative"
                )
            
            result = await CarbonService.calculate_emission_by_mode(distance_km, mode)
            
            return {
                "co2_grams": result["total_co2_grams"],
                "co2_kg": result["total_co2_kg"],
                "emission_factor_g_per_km": result["emission_factor_g_per_km"],
                "distance_km": result["distance_km"],
                "mode": mode,
                "emission_mode": result["mode"],
                "data_source": result["data_source"]
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to calculate route carbon: {str(e)}"
            )
    
    @staticmethod
    def extract_transit_details(leg: Dict[str, Any]) -> Dict[str, Any]:
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
            
            return {
                "transit_steps": transit_steps,
                "walking_steps": walking_steps,
                "total_transit_steps": len(transit_steps),
                "total_walking_steps": len(walking_steps)
            }
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
            
            carbon_data = await MapService.calculate_route_carbon(distance_km, mode)
            
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
                "priority_score": duration_min
            }
            
            if mode == "transit":
                result["transit_info"] = MapService.extract_transit_details(leg)
            
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
                driving_result = await maps.get_directions(origin, destination, mode="driving", alternatives=True, language=language)
                transit_result = await maps.get_directions(origin, destination, mode="transit", alternatives=True, language=language)
                walking_result = await maps.get_directions(origin, destination, mode="walking", language=language)
                bicycling_result = await maps.get_directions(origin, destination, mode="bicycling", language=language)
                
                all_routes = []
                
                if driving_result.get("status") == "OK" and driving_result.get("routes"):
                    for idx, route in enumerate(driving_result["routes"]):
                        display_name = "Driving (fastest)" if idx == 0 else f"Driving (option {idx+1})"
                        route_type = "fastest_driving" if idx == 0 else f"alternative_driving_{idx}"
                        
                        route_data = await MapService.process_route_data(
                            route, "driving", route_type, display_name
                        )
                        all_routes.append(route_data)
                
                if transit_result.get("status") == "OK" and transit_result.get("routes"):
                    for idx, route in enumerate(transit_result["routes"]):
                        display_name = "Public transport"
                        route_type = "transit" if idx == 0 else f"alternative_transit_{idx}"
                        
                        route_data = await MapService.process_route_data(
                            route, "transit", route_type, display_name
                        )
                        all_routes.append(route_data)
                
                if walking_result.get("status") == "OK" and walking_result.get("routes"):
                    route = walking_result["routes"][0]
                    leg = route["legs"][0]
                    distance_km = leg["distance"]["value"] / 1000
                    
                    if distance_km <= 3.0:
                        route_data = await MapService.process_route_data(
                            route, "walking", "walking", "Walking"
                        )
                        all_routes.append(route_data)
                
                if bicycling_result.get("status") == "OK" and bicycling_result.get("routes"):
                    route = bicycling_result["routes"][0]
                    route_data = await MapService.process_route_data(
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
                
                smart_route = MapService._find_smart_route(
                    all_routes, fastest_route, max_time_ratio
                )
                
                if smart_route:
                    results["routes"]["smart_combination"] = smart_route
                
                results["recommendation"] = MapService._generate_recommendation(
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
    def _find_smart_route(
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
    def _generate_recommendation(
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
    
    @staticmethod
    async def compare_all_route_options(
        origin: str,
        destination: str,
        max_time_ratio: float = 1.5
    ) -> Dict[str, Any]:
        """Compare all available route options with carbon emissions"""
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
            
            maps = await create_maps_client()
            
            try:
                driving = await maps.get_directions(origin, destination, mode="driving", alternatives=True)
                walking = await maps.get_directions(origin, destination, mode="walking")
                bicycling = await maps.get_directions(origin, destination, mode="bicycling")
                transit = await maps.get_directions(origin, destination, mode="transit")
                
                all_options = []
                
                if driving.get("status") == "OK":
                    for idx, route in enumerate(driving.get("routes", [])):
                        leg = route["legs"][0]
                        distance_km = leg["distance"]["value"] / 1000
                        duration_sec = leg["duration"]["value"]
                        
                        carbon = await MapService.calculate_route_carbon(distance_km, "driving")
                        
                        all_options.append({
                            "type": "fastest" if idx == 0 else "alternative_driving",
                            "mode": "driving",
                            "mode_display": "🚗 Car",
                            "distance_km": round(distance_km, 2),
                            "duration_minutes": round(duration_sec / 60, 1),
                            "duration_text": leg["duration"]["text"],
                            "carbon_emission": carbon,
                            "route_data": route,
                            "is_fastest": idx == 0,
                            "eco_score": 0
                        })
                
                if walking.get("status") == "OK":
                    leg = walking["routes"][0]["legs"][0]
                    distance_km = leg["distance"]["value"] / 1000
                    duration_sec = leg["duration"]["value"]
                    
                    carbon = await MapService.calculate_route_carbon(distance_km, "walking")
                    
                    all_options.append({
                        "type": "walking",
                        "mode": "walking",
                        "mode_display": "🚶 Walking",
                        "distance_km": round(distance_km, 2),
                        "duration_minutes": round(duration_sec / 60, 1),
                        "duration_text": leg["duration"]["text"],
                        "carbon_emission": carbon,
                        "route_data": walking["routes"][0],
                        "is_fastest": False,
                        "eco_score": 100,
                        "health_benefit": f"+{int(distance_km * 60)} calories"
                    })
                
                if bicycling.get("status") == "OK":
                    leg = bicycling["routes"][0]["legs"][0]
                    distance_km = leg["distance"]["value"] / 1000
                    duration_sec = leg["duration"]["value"]
                    
                    carbon = await MapService.calculate_route_carbon(distance_km, "bicycling")
                    
                    all_options.append({
                        "type": "bicycling",
                        "mode": "bicycling",
                        "mode_display": "🚴 Bicycle",
                        "distance_km": round(distance_km, 2),
                        "duration_minutes": round(duration_sec / 60, 1),
                        "duration_text": leg["duration"]["text"],
                        "carbon_emission": carbon,
                        "route_data": bicycling["routes"][0],
                        "is_fastest": False,
                        "eco_score": 100,
                        "health_benefit": f"+{int(distance_km * 120)} calories"
                    })
                
                if transit.get("status") == "OK":
                    leg = transit["routes"][0]["legs"][0]
                    distance_km = leg["distance"]["value"] / 1000
                    duration_sec = leg["duration"]["value"]
                    
                    carbon = await MapService.calculate_route_carbon(distance_km, "transit")
                    
                    all_options.append({
                        "type": "transit",
                        "mode": "transit",
                        "mode_display": "🚌 Bus/Train",
                        "distance_km": round(distance_km, 2),
                        "duration_minutes": round(duration_sec / 60, 1),
                        "duration_text": leg["duration"]["text"],
                        "carbon_emission": carbon,
                        "route_data": transit["routes"][0],
                        "is_fastest": False,
                        "eco_score": 85,
                        "transit_details": MapService.extract_transit_details(leg)
                    })
                
                if not all_options:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No routes found between the specified locations"
                    )
                
                fastest_route = min(all_options, key=lambda x: x["duration_minutes"])
                lowest_carbon = min(all_options, key=lambda x: x["carbon_emission"]["co2_kg"])
                
                smart_route = None
                fastest_time = fastest_route["duration_minutes"]
                
                for option in all_options:
                    if option["mode"] == "transit":
                        time_ratio = option["duration_minutes"] / fastest_time
                        
                        if time_ratio <= max_time_ratio:
                            driving_option = next((x for x in all_options if x["mode"] == "driving"), None)
                            if driving_option:
                                carbon_saving = driving_option["carbon_emission"]["co2_kg"] - option["carbon_emission"]["co2_kg"]
                                carbon_saving_percent = (carbon_saving / driving_option["carbon_emission"]["co2_kg"] * 100) if driving_option["carbon_emission"]["co2_kg"] > 0 else 0
                                
                                option["carbon_saving_kg"] = round(carbon_saving, 3)
                                option["carbon_saving_percent"] = round(carbon_saving_percent, 1)
                                option["is_recommended"] = carbon_saving_percent > 50
                                
                                if not smart_route or option["carbon_emission"]["co2_kg"] < smart_route["carbon_emission"]["co2_kg"]:
                                    smart_route = option
                
                return {
                    "summary": {
                        "origin": origin,
                        "destination": destination,
                        "total_options": len(all_options)
                    },
                    "fastest_route": {
                        **fastest_route,
                        "highlight": "⚡ FASTEST"
                    },
                    "lowest_carbon_route": {
                        **lowest_carbon,
                        "highlight": "🌱 LOWEST CARBON",
                        "carbon_saved_vs_driving": round(
                            next((x for x in all_options if x["mode"] == "driving"), {"carbon_emission": {"co2_kg": 0}})["carbon_emission"]["co2_kg"] 
                            - lowest_carbon["carbon_emission"]["co2_kg"], 
                            3
                        )
                    },
                    "smart_route": {
                        **smart_route,
                        "highlight": "🧠 SMART (Balance time & environment)"
                    } if smart_route else None,
                    "all_options": sorted(all_options, key=lambda x: x["duration_minutes"])
                }
            
            finally:
                await maps.close()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to compare route options: {str(e)}"
            )
    
    @staticmethod
    async def calculate_eco_route(
        origin: str,
        destination: str,
        avoid_highways: bool = True,
        avoid_tolls: bool = True
    ) -> Dict[str, Any]:
        """Calculate eco-friendly driving route with carbon estimation"""
        try:
            if not origin or not destination:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Origin and destination are required"
                )
            
            maps = await create_maps_client()
            
            try:
                avoid_features = []
                if avoid_highways:
                    avoid_features.append("highways")
                if avoid_tolls:
                    avoid_features.append("tolls")
                
                result = await maps.get_directions(
                    origin=origin,
                    destination=destination,
                    mode="driving",
                    avoid=avoid_features if avoid_features else None,
                    alternatives=True
                )
                
                if result.get("status") == "OK" and result.get("routes"):
                    for route in result["routes"]:
                        total_distance_km = route["legs"][0]["distance"]["value"] / 1000
                        carbon_data = await MapService.calculate_route_carbon(total_distance_km, "driving")
                        
                        route["eco_metrics"] = {
                            "estimated_co2_kg": carbon_data["co2_kg"],
                            "distance_km": round(total_distance_km, 2),
                            "emission_factor": carbon_data["emission_factor_g_per_km"]
                        }
                elif result.get("status") == "ZERO_RESULTS":
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No routes found with the specified constraints"
                    )
                elif result.get("status") != "OK":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Google Maps API returned status: {result.get('status')}"
                    )
                
                return result
            
            finally:
                await maps.close()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to calculate eco route: {str(e)}"
            )