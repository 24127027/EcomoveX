import httpx
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from utils.config import settings


class GoogleMapsAPI:
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GOOGLE_MAPS_API_KEY
        if not self.api_key:
            raise ValueError("Google Maps API key is required")
        
        self.base_url = "https://maps.googleapis.com/maps/api"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        await self.client.aclose()
    
    async def search_places(
        self,
        query: str,
        location: Optional[Tuple[float, float]] = None,
        radius: Optional[int] = None,
        type: Optional[str] = None,
        language: str = "vi",
        region: str = "vn"
    ) -> Dict[str, Any]:
        """Search for places using text query"""
        params = {
            "query": query,
            "language": language,
            "region": region,
            "key": self.api_key
        }
        
        if location:
            params["location"] = f"{location[0]},{location[1]}"
        if radius:
            params["radius"] = radius
        if type:
            params["type"] = type
        
        url = f"{self.base_url}/place/textsearch/json"
        response = await self.client.get(url, params=params)
        return response.json()
    
    async def nearby_search(
        self,
        lat: float,
        lng: float,
        radius: int = 1000,
        type: Optional[str] = None,
        keyword: Optional[str] = None,
        language: str = "vi"
    ) -> Dict[str, Any]:
        """Search for places nearby a location"""
        params = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "language": language,
            "key": self.api_key
        }
        
        if type:
            params["type"] = type
        if keyword:
            params["keyword"] = keyword
        
        url = f"{self.base_url}/place/nearbysearch/json"
        response = await self.client.get(url, params=params)
        return response.json()
    
    async def get_place_details(
        self,
        place_id: str,
        fields: Optional[List[str]] = None,
        language: str = "vi"
    ) -> Dict[str, Any]:
        """Get detailed information about a place"""
        params = {
            "place_id": place_id,
            "language": language,
            "key": self.api_key
        }
        
        if fields:
            params["fields"] = ",".join(fields)
        else:
            params["fields"] = "name,formatted_address,geometry,rating,photos,opening_hours,website,formatted_phone_number,reviews,price_level,types"
        
        url = f"{self.base_url}/place/details/json"
        response = await self.client.get(url, params=params)
        return response.json()
    
    async def get_directions(
        self,
        origin: str,
        destination: str,
        mode: str = "driving",
        waypoints: Optional[List[str]] = None,
        alternatives: bool = False,
        avoid: Optional[List[str]] = None,
        language: str = "vi"
    ) -> Dict[str, Any]:
        """Get directions between locations"""
        params = {
            "origin": origin,
            "destination": destination,
            "mode": mode,
            "alternatives": str(alternatives).lower(),
            "language": language,
            "key": self.api_key
        }
        
        if waypoints:
            params["waypoints"] = "optimize:true|" + "|".join(waypoints)
        if avoid:
            params["avoid"] = "|".join(avoid)
        
        url = f"{self.base_url}/directions/json"
        response = await self.client.get(url, params=params)
        return response.json()
    
    async def optimize_route(
        self,
        origin: str,
        destination: str,
        waypoints: List[str],
        mode: str = "driving",
        language: str = "vi"
    ) -> Dict[str, Any]:
        """Optimize route with multiple waypoints"""
        params = {
            "origin": origin,
            "destination": destination,
            "waypoints": "optimize:true|" + "|".join(waypoints),
            "mode": mode,
            "language": language,
            "key": self.api_key
        }
        
        url = f"{self.base_url}/directions/json"
        response = await self.client.get(url, params=params)
        
        result = response.json()
        if result.get("status") == "OK" and result.get("routes"):
            route = result["routes"][0]
            if "waypoint_order" in route:
                result["optimized_waypoint_order"] = route["waypoint_order"]
        
        return result
    
    async def get_air_quality(
        self,
        lat: float,
        lng: float,
        language_code: str = "vi"
    ) -> Dict[str, Any]:
        """Get current air quality data"""
        payload = {
            "location": {
                "latitude": lat,
                "longitude": lng
            },
            "languageCode": language_code
        }
        
        url = "https://airquality.googleapis.com/v1/currentConditions:lookup"
        response = await self.client.post(
            url,
            params={"key": self.api_key},
            json=payload
        )
        return response.json()
    
    async def get_air_quality_history(
        self,
        lat: float,
        lng: float,
        hours: int = 24,
        language_code: str = "vi"
    ) -> Dict[str, Any]:
        """Get historical air quality data"""
        payload = {
            "location": {
                "latitude": lat,
                "longitude": lng
            },
            "hours": hours,
            "languageCode": language_code
        }
        
        url = "https://airquality.googleapis.com/v1/history:lookup"
        response = await self.client.post(
            url,
            params={"key": self.api_key},
            json=payload
        )
        return response.json()
    
    async def get_air_quality_with_pollutants(
        self,
        lat: float,
        lng: float,
        extra_computations: Optional[List[str]] = None,
        language_code: str = "vi"
    ) -> Dict[str, Any]:
        """
        Get detailed air quality with specific pollutant information
        
        Args:
            lat: Latitude
            lng: Longitude
            extra_computations: List of extra computations like ['POLLUTANT_ADDITIONAL_INFO', 'DOMINANT_POLLUTANT_CONCENTRATION']
            language_code: Language code (default: Vietnamese)
        
        Returns:
            Detailed air quality data with pollutant concentrations
        """
        payload = {
            "location": {
                "latitude": lat,
                "longitude": lng
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
        return response.json()
    
    async def get_air_quality_heatmap(
        self,
        lat: float,
        lng: float,
        zoom: int = 12
    ) -> Dict[str, Any]:
        """
        Get air quality heatmap tile information
        
        Args:
            lat: Latitude
            lng: Longitude
            zoom: Map zoom level (0-16)
        
        Returns:
            Heatmap tile URL and metadata
        """
        # Calculate tile coordinates from lat/lng
        import math
        n = 2.0 ** zoom
        x = int((lng + 180.0) / 360.0 * n)
        y = int((1.0 - math.log(math.tan(math.radians(lat)) + (1 / math.cos(math.radians(lat)))) / math.pi) / 2.0 * n)
        
        url = f"https://airquality.googleapis.com/v1/mapTypes/UAQI_RED_GREEN/heatmapTiles/{zoom}/{x}/{y}"
        response = await self.client.get(url, params={"key": self.api_key})
        
        return {
            "tile_url": url,
            "zoom": zoom,
            "x": x,
            "y": y,
            "location": {"lat": lat, "lng": lng},
            "status_code": response.status_code
        }
        
    async def get_weather_forecast(
        self,
        lat: float,
        lng: float
    ) -> Dict[str, Any]:
        """Get weather forecast (uses geocoding + external weather API)"""
        geocode_result = await self.reverse_geocode(lat, lng)
        
        location_name = "Unknown"
        if geocode_result.get("status") == "OK" and geocode_result.get("results"):
            location_name = geocode_result["results"][0].get("formatted_address", "Unknown")
        
        return {
            "location": {
                "lat": lat,
                "lng": lng,
                "name": location_name
            },
            "message": "Use external weather API like OpenWeatherMap for detailed forecast"
        }
    
    async def reverse_geocode(
        self,
        lat: float,
        lng: float,
        language: str = "vi"
    ) -> Dict[str, Any]:
        """Convert coordinates to address"""
        params = {
            "latlng": f"{lat},{lng}",
            "language": language,
            "key": self.api_key
        }
        
        url = f"{self.base_url}/geocode/json"
        response = await self.client.get(url, params=params)
        return response.json()
    
    async def geocode(
        self,
        address: str,
        language: str = "vi",
        region: str = "vn"
    ) -> Dict[str, Any]:
        """Convert address to coordinates"""
        params = {
            "address": address,
            "language": language,
            "region": region,
            "key": self.api_key
        }
        
        url = f"{self.base_url}/geocode/json"
        response = await self.client.get(url, params=params)
        return response.json()
    
    async def calculate_eco_route(
        self,
        origin: str,
        destination: str,
        avoid_highways: bool = True,
        avoid_tolls: bool = True
    ) -> Dict[str, Any]:
        """Calculate eco-friendly route with CO2 estimation"""
        avoid_features = []
        if avoid_highways:
            avoid_features.append("highways")
        if avoid_tolls:
            avoid_features.append("tolls")
        
        result = await self.get_directions(
            origin=origin,
            destination=destination,
            mode="driving",
            avoid=avoid_features if avoid_features else None,
            alternatives=True
        )
        
        if result.get("status") == "OK" and result.get("routes"):
            for route in result["routes"]:
                total_distance_km = route["legs"][0]["distance"]["value"] / 1000
                estimated_co2_kg = (total_distance_km * 120) / 1000
                route["eco_metrics"] = {
                    "estimated_co2_kg": round(estimated_co2_kg, 2),
                    "distance_km": round(total_distance_km, 2)
                }
        
        return result
    
    async def _calculate_carbon_emission(
        self,
        distance_km: float,
        mode: str
    ) -> Dict[str, Any]:
        """
        Calculate carbon emission based on transport mode using Vietnam-specific data
        
        Uses real emission factors from:
        - Climatiq Data Explorer (Vietnam transport sector)
        - Electricity Maps API (for electric vehicles)
        - IPCC Guidelines
        
        Emission factors for Vietnam (gCO2/km):
        - car/driving: 192g (petrol car)
        - motorbike: 84g (motorbike 125cc)
        - bus/transit: 68g (diesel bus)
        - train: 41g (diesel train)
        - metro/subway: 35g (electric metro)
        - bicycle: 0g
        - walking: 0g
        """
        # Import CarbonService to avoid circular dependency
        from services.carbon_service import CarbonService
        
        # Calculate emission using Vietnam-specific factors
        result = await CarbonService.calculate_emission_by_mode(distance_km, mode)
        
        return {
            "co2_grams": result["total_co2_grams"],
            "co2_kg": result["total_co2_kg"],
            "emission_factor_g_per_km": result["emission_factor_g_per_km"],
            "distance_km": result["distance_km"],
            "mode": mode,
            "emission_mode": result["mode"],  # Actual mode used for calculation
            "data_source": result["data_source"]
        }
    
    async def compare_routes_all_options(
        self,
        origin: str,
        destination: str,
        max_time_ratio: float = 1.5
    ) -> Dict[str, Any]:
        """
        So sánh TẤT CẢ phương án di chuyển:
        1. Quãng đường ngắn nhất (thời gian)
        2. Quãng đường carbon emission thấp nhất
        3. Phương án thông minh (kết hợp đi bộ + public transport)
        
        Args:
            origin: Điểm xuất phát
            destination: Điểm đến
            max_time_ratio: Tỷ lệ thời gian tối đa so với route nhanh nhất (1.5 = chậm hơn 50% vẫn được)
        
        Returns:
            Dict chứa tất cả options với carbon emission và thời gian
        """
        # 1. Lấy tất cả các phương án di chuyển song song
        results = {}
        
        # Driving (xe hơi)
        driving = await self.get_directions(origin, destination, mode="driving", alternatives=True)
        results["driving"] = driving
        
        # Walking (đi bộ)
        walking = await self.get_directions(origin, destination, mode="walking")
        results["walking"] = walking
        
        # Bicycling (xe đạp)
        bicycling = await self.get_directions(origin, destination, mode="bicycling")
        results["bicycling"] = bicycling
        
        # Transit (xe bus/tàu)
        transit = await self.get_directions(origin, destination, mode="transit")
        results["transit"] = transit
        
        # 2. Process and calculate carbon for all routes
        all_options = []
        
        # Process driving routes
        if results["driving"].get("status") == "OK":
            for idx, route in enumerate(results["driving"].get("routes", [])):
                leg = route["legs"][0]
                distance_km = leg["distance"]["value"] / 1000
                duration_sec = leg["duration"]["value"]
                
                carbon = await self._calculate_carbon_emission(distance_km, "driving")
                
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
                    "eco_score": 0  # Will be calculated later
                })
        
        # Process walking
        if results["walking"].get("status") == "OK":
            leg = results["walking"]["routes"][0]["legs"][0]
            distance_km = leg["distance"]["value"] / 1000
            duration_sec = leg["duration"]["value"]
            
            carbon = await self._calculate_carbon_emission(distance_km, "walking")
            
            all_options.append({
                "type": "walking",
                "mode": "walking",
                "mode_display": "🚶 Walking",
                "distance_km": round(distance_km, 2),
                "duration_minutes": round(duration_sec / 60, 1),
                "duration_text": leg["duration"]["text"],
                "carbon_emission": carbon,
                "route_data": results["walking"]["routes"][0],
                "is_fastest": False,
                "eco_score": 100,  # Perfect eco score
                "health_benefit": f"+{int(distance_km * 60)} calories"
            })
        
        # Process bicycling
        if results["bicycling"].get("status") == "OK":
            leg = results["bicycling"]["routes"][0]["legs"][0]
            distance_km = leg["distance"]["value"] / 1000
            duration_sec = leg["duration"]["value"]
            
            carbon = await self._calculate_carbon_emission(distance_km, "bicycling")
            
            all_options.append({
                "type": "bicycling",
                "mode": "bicycling",
                "mode_display": "🚴 Bicycle",
                "distance_km": round(distance_km, 2),
                "duration_minutes": round(duration_sec / 60, 1),
                "duration_text": leg["duration"]["text"],
                "carbon_emission": carbon,
                "route_data": results["bicycling"]["routes"][0],
                "is_fastest": False,
                "eco_score": 100,  # Perfect eco score
                "health_benefit": f"+{int(distance_km * 120)} calories"
            })
        
        # Process transit
        if results["transit"].get("status") == "OK":
            leg = results["transit"]["routes"][0]["legs"][0]
            distance_km = leg["distance"]["value"] / 1000
            duration_sec = leg["duration"]["value"]
            
            carbon = await self._calculate_carbon_emission(distance_km, "transit")
            
            all_options.append({
                "type": "transit",
                "mode": "transit",
                "mode_display": "🚌 Bus/Train",
                "distance_km": round(distance_km, 2),
                "duration_minutes": round(duration_sec / 60, 1),
                "duration_text": leg["duration"]["text"],
                "carbon_emission": carbon,
                "route_data": results["transit"]["routes"][0],
                "is_fastest": False,
                "eco_score": 85,  # Very good eco score
                "transit_details": self._extract_transit_details(leg)
            })
        
        # 3. Find fastest route and lowest carbon route
        if not all_options:
            return {"error": "No routes found"}
        
        fastest_route = min(all_options, key=lambda x: x["duration_minutes"])
        lowest_carbon = min(all_options, key=lambda x: x["carbon_emission"]["co2_kg"])
        
        # 4. Find SMART ROUTE option
        # Criteria: Combine transit + walking, time not too long
        smart_route = None
        fastest_time = fastest_route["duration_minutes"]
        
        for option in all_options:
            # Only consider transit (already includes walking)
            if option["mode"] == "transit":
                time_ratio = option["duration_minutes"] / fastest_time
                
                # If time difference is acceptable (< max_time_ratio)
                # AND carbon is significantly lower than driving
                if time_ratio <= max_time_ratio:
                    driving_carbon = next((x for x in all_options if x["mode"] == "driving"), None)
                    if driving_carbon:
                        carbon_saving = driving_carbon["carbon_emission"]["co2_kg"] - option["carbon_emission"]["co2_kg"]
                        carbon_saving_percent = (carbon_saving / driving_carbon["carbon_emission"]["co2_kg"]) * 100
                        
                        option["smart_route_info"] = {
                            "time_difference_minutes": round(option["duration_minutes"] - fastest_time, 1),
                            "time_ratio": round(time_ratio, 2),
                            "carbon_saving_kg": round(carbon_saving, 3),
                            "carbon_saving_percent": round(carbon_saving_percent, 1),
                            "is_recommended": carbon_saving_percent > 50  # Saves > 50% CO2
                        }
                        
                        if not smart_route or option["carbon_emission"]["co2_kg"] < smart_route["carbon_emission"]["co2_kg"]:
                            smart_route = option
        
        # 5. Return results
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
    
    def _extract_transit_details(self, leg: Dict[str, Any]) -> Dict[str, Any]:
        """Extract transit step details (bus/train lines, stops, etc.)"""
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
    
    async def find_three_optimal_routes(
        self,
        origin: str,
        destination: str,
        max_time_ratio: float = 1.3,
        language: str = "vi"
    ) -> Dict[str, Any]:
        """
        Find 3 optimal routes based on different criteria:
        1. Fastest route (shortest time)
        2. Lowest carbon emission route
        3. Smart combination route (walking + public transport, if available)
        
        Args:
            origin: Starting location
            destination: Destination location
            max_time_ratio: Maximum time ratio for smart route compared to fastest (default: 1.3x)
            language: Language for directions
        
        Returns:
            Dictionary with 3 routes and recommendations
        """
        results = {
            "origin": origin,
            "destination": destination,
            "routes": {},
            "recommendation": None
        }
        
        # Get all available routes for different modes
        driving_result = await self.get_directions(origin, destination, mode="driving", alternatives=True, language=language)
        transit_result = await self.get_directions(origin, destination, mode="transit", alternatives=True, language=language)
        walking_result = await self.get_directions(origin, destination, mode="walking", language=language)
        bicycling_result = await self.get_directions(origin, destination, mode="bicycling", language=language)
        
        all_routes = []
        
        # Process driving routes
        if driving_result.get("status") == "OK" and driving_result.get("routes"):
            for idx, route in enumerate(driving_result["routes"]):
                leg = route["legs"][0]
                distance_km = leg["distance"]["value"] / 1000
                duration_min = leg["duration"]["value"] / 60
                
                carbon_data = await self._calculate_carbon_emission(distance_km, "driving")
                
                all_routes.append({
                    "type": "fastest_driving" if idx == 0 else f"alternative_driving_{idx}",
                    "mode": "driving",
                    "display_name": "Lái xe (nhanh nhất)" if idx == 0 else f"Lái xe (lựa chọn {idx+1})",
                    "distance_km": distance_km,
                    "duration_min": duration_min,
                    "duration_text": leg["duration"]["text"],
                    "carbon_kg": carbon_data["co2_kg"],
                    "carbon_grams": carbon_data["co2_grams"],
                    "emission_factor": carbon_data["emission_factor_g_per_km"],
                    "route_details": route,
                    "priority_score": duration_min  # Lower is better
                })
        
        # Process transit routes
        if transit_result.get("status") == "OK" and transit_result.get("routes"):
            for idx, route in enumerate(transit_result["routes"]):
                leg = route["legs"][0]
                distance_km = leg["distance"]["value"] / 1000
                duration_min = leg["duration"]["value"] / 60
                
                carbon_data = await self._calculate_carbon_emission(distance_km, "transit")
                
                # Parse transit details
                transit_info = self._extract_transit_details(route["legs"][0])
                
                all_routes.append({
                    "type": "transit" if idx == 0 else f"alternative_transit_{idx}",
                    "mode": "transit",
                    "display_name": "Phương tiện công cộng",
                    "distance_km": distance_km,
                    "duration_min": duration_min,
                    "duration_text": leg["duration"]["text"],
                    "carbon_kg": carbon_data["co2_kg"],
                    "carbon_grams": carbon_data["co2_grams"],
                    "emission_factor": carbon_data["emission_factor_g_per_km"],
                    "route_details": route,
                    "transit_info": transit_info,
                    "priority_score": duration_min
                })
        
        # Process walking route
        if walking_result.get("status") == "OK" and walking_result.get("routes"):
            route = walking_result["routes"][0]
            leg = route["legs"][0]
            distance_km = leg["distance"]["value"] / 1000
            duration_min = leg["duration"]["value"] / 60
            
            carbon_data = await self._calculate_carbon_emission(distance_km, "walking")
            
            # Only include walking if distance is reasonable (< 3km)
            if distance_km <= 3.0:
                all_routes.append({
                    "type": "walking",
                    "mode": "walking",
                    "display_name": "Đi bộ",
                    "distance_km": distance_km,
                    "duration_min": duration_min,
                    "duration_text": leg["duration"]["text"],
                    "carbon_kg": carbon_data["co2_kg"],
                    "carbon_grams": carbon_data["co2_grams"],
                    "emission_factor": carbon_data["emission_factor_g_per_km"],
                    "route_details": route,
                    "priority_score": duration_min
                })
        
        # Process bicycling route
        if bicycling_result.get("status") == "OK" and bicycling_result.get("routes"):
            route = bicycling_result["routes"][0]
            leg = route["legs"][0]
            distance_km = leg["distance"]["value"] / 1000
            duration_min = leg["duration"]["value"] / 60
            
            carbon_data = await self._calculate_carbon_emission(distance_km, "bicycling")
            
            all_routes.append({
                "type": "bicycling",
                "mode": "bicycling",
                "display_name": "Đạp xe",
                "distance_km": distance_km,
                "duration_min": duration_min,
                "duration_text": leg["duration"]["text"],
                "carbon_kg": carbon_data["co2_kg"],
                "carbon_grams": carbon_data["co2_grams"],
                "emission_factor": carbon_data["emission_factor_g_per_km"],
                "route_details": route,
                "priority_score": duration_min
            })
        
        # Find the 3 optimal routes
        if not all_routes:
            return {
                "status": "NO_ROUTES_FOUND",
                "message": "Không tìm thấy tuyến đường phù hợp"
            }
        
        # 1. FASTEST ROUTE (shortest time)
        fastest_route = min(all_routes, key=lambda x: x["duration_min"])
        results["routes"]["fastest"] = {
            **fastest_route,
            "reason": "Tuyến đường nhanh nhất"
        }
        
        # 2. LOWEST CARBON ROUTE (lowest emission)
        lowest_carbon_route = min(all_routes, key=lambda x: x["carbon_kg"])
        results["routes"]["lowest_carbon"] = {
            **lowest_carbon_route,
            "reason": "Tuyến đường ít carbon nhất"
        }
        
        # 3. SMART ROUTE (walking + transit combination, if available and reasonable)
        # Smart route criteria (in priority order):
        # 1. Transit with reasonable time (kết hợp đi bộ + xe công cộng)
        # 2. Walking if distance is short (<3km) and time reasonable
        # 3. Bicycling if available and time reasonable
        smart_route = None
        transit_routes = [r for r in all_routes if r["mode"] == "transit"]
        
        # First priority: Transit routes (if available)
        if transit_routes:
            # Choose transit with best balance (lowest carbon among transit options)
            best_transit = min(transit_routes, key=lambda x: x["carbon_kg"])
            
            # Accept transit if it's significantly lower carbon than driving
            driving_routes = [r for r in all_routes if r["mode"] == "driving"]
            if driving_routes:
                best_driving = min(driving_routes, key=lambda x: x["duration_min"])
                carbon_saving_percent = ((best_driving["carbon_kg"] - best_transit["carbon_kg"]) / best_driving["carbon_kg"] * 100) if best_driving["carbon_kg"] > 0 else 0
                
                # Accept transit if saves >30% carbon OR within acceptable time
                max_acceptable_time = fastest_route["duration_min"] * max_time_ratio
                
                if carbon_saving_percent > 30 or best_transit["duration_min"] <= max_acceptable_time:
                    smart_route = best_transit
                    results["routes"]["smart_combination"] = {
                        **smart_route,
                        "reason": f"Tuyến thông minh (kết hợp đi bộ + xe công cộng, tiết kiệm {carbon_saving_percent:.1f}% carbon)",
                        "time_comparison": {
                            "vs_fastest_min": round(smart_route["duration_min"] - fastest_route["duration_min"], 1),
                            "vs_fastest_percent": round((smart_route["duration_min"] / fastest_route["duration_min"] - 1) * 100, 1)
                        },
                        "carbon_comparison": {
                            "vs_driving_kg": round(best_driving["carbon_kg"] - smart_route["carbon_kg"], 3),
                            "vs_driving_percent": round(carbon_saving_percent, 1)
                        }
                    }
        
        # Second priority: Walking (if distance is short and time reasonable)
        if not smart_route:
            walking_routes = [r for r in all_routes if r["mode"] == "walking"]
            
            if walking_routes:
                walk_route = walking_routes[0]
                max_acceptable_time = fastest_route["duration_min"] * max_time_ratio
                
                # Accept walking if distance <3km AND time reasonable
                if walk_route["distance_km"] <= 3.0 and walk_route["duration_min"] <= max_acceptable_time:
                    smart_route = walk_route
                    results["routes"]["smart_combination"] = {
                        **smart_route,
                        "reason": "Tuyến thông minh (đi bộ - khoảng cách ngắn, 0 carbon)",
                        "time_comparison": {
                            "vs_fastest_min": round(smart_route["duration_min"] - fastest_route["duration_min"], 1),
                            "vs_fastest_percent": round((smart_route["duration_min"] / fastest_route["duration_min"] - 1) * 100, 1)
                        }
                    }
        
        # Third priority: Bicycling (if available and time reasonable)
        if not smart_route:
            bicycling_routes = [r for r in all_routes if r["mode"] == "bicycling"]
            
            if bicycling_routes:
                bike_route = bicycling_routes[0]
                max_acceptable_time = fastest_route["duration_min"] * max_time_ratio
                
                if bike_route["duration_min"] <= max_acceptable_time:
                    smart_route = bike_route
                    results["routes"]["smart_combination"] = {
                        **smart_route,
                        "reason": "Tuyến thông minh (đạp xe - 0 carbon)",
                        "time_comparison": {
                            "vs_fastest_min": round(smart_route["duration_min"] - fastest_route["duration_min"], 1),
                            "vs_fastest_percent": round((smart_route["duration_min"] / fastest_route["duration_min"] - 1) * 100, 1)
                        }
                    }

        
        # Determine overall recommendation
        carbon_savings_vs_fastest = fastest_route["carbon_kg"] - lowest_carbon_route["carbon_kg"]
        carbon_savings_percent = (carbon_savings_vs_fastest / fastest_route["carbon_kg"] * 100) if fastest_route["carbon_kg"] > 0 else 0
        
        if carbon_savings_percent > 50 and lowest_carbon_route["duration_min"] <= fastest_route["duration_min"] * 1.5:
            results["recommendation"] = "lowest_carbon"
            results["recommendation_reason"] = f"Tiết kiệm {carbon_savings_percent:.1f}% carbon, chỉ chậm hơn {lowest_carbon_route['duration_min'] - fastest_route['duration_min']:.1f} phút"
        elif "smart_combination" in results["routes"] and results["routes"]["smart_combination"]["carbon_kg"] < fastest_route["carbon_kg"] * 0.7:
            results["recommendation"] = "smart_combination"
            results["recommendation_reason"] = "Cân bằng tốt giữa thời gian và carbon"
        else:
            results["recommendation"] = "fastest"
            results["recommendation_reason"] = "Tiết kiệm thời gian tối đa"
        
        results["status"] = "OK"
        results["total_routes_analyzed"] = len(all_routes)
        
        return results


async def create_maps_client(api_key: Optional[str] = None) -> GoogleMapsAPI:
    return GoogleMapsAPI(api_key=api_key)