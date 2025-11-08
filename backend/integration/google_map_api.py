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
    
    async def autocomplete_place(
        self,
        input_text: str,
        location: Optional[Tuple[float, float]] = None,
        radius: Optional[int] = None,
        types: Optional[str] = None,
        language: str = "vi",
        components: str = "country:vn"
    ) -> Dict[str, Any]:
        """
        Place Autocomplete - Search bar suggestions như Google Maps
        
        Args:
            input_text: Text người dùng đang gõ (vd: "Hồ Hoàn Kiếm")
            location: Vị trí hiện tại để ưu tiên kết quả gần (lat, lng)
            radius: Bán kính tìm kiếm từ location (meters)
            types: Loại địa điểm: "geocode", "address", "establishment", "(regions)", "(cities)"
            language: Ngôn ngữ kết quả
            components: Giới hạn theo quốc gia (country:vn)
        
        Returns:
            List các suggestions với place_id, description, structured_formatting
        """
        params = {
            "input": input_text,
            "language": language,
            "key": self.api_key
        }
        
        if location:
            params["location"] = f"{location[0]},{location[1]}"
        if radius:
            params["radius"] = radius
        if types:
            params["types"] = types
        if components:
            params["components"] = components
        
        url = f"{self.base_url}/place/autocomplete/json"
        response = await self.client.get(url, params=params)
        return response.json()
    
    async def query_autocomplete(
        self,
        input_text: str,
        location: Optional[Tuple[float, float]] = None,
        radius: Optional[int] = None,
        language: str = "vi"
    ) -> Dict[str, Any]:
        """
        Query Autocomplete - Tìm kiếm địa điểm + queries (linh hoạt hơn)
        
        Khác với Place Autocomplete: trả về cả queries không chỉ places
        VD: "nhà hàng gần đây", "quán cafe ở Hà Nội"
        
        Args:
            input_text: Text người dùng đang gõ
            location: Vị trí hiện tại (lat, lng)
            radius: Bán kính tìm kiếm (meters)
            language: Ngôn ngữ
        
        Returns:
            List suggestions bao gồm cả queries và places
        """
        params = {
            "input": input_text,
            "language": language,
            "key": self.api_key
        }
        
        if location:
            params["location"] = f"{location[0]},{location[1]}"
        if radius:
            params["radius"] = radius
        
        url = f"{self.base_url}/place/queryautocomplete/json"
        response = await self.client.get(url, params=params)
        return response.json()
    
    async def get_place_details_from_autocomplete(
        self,
        place_id: str,
        fields: Optional[List[str]] = None,
        language: str = "vi"
    ) -> Dict[str, Any]:
        """
        Lấy chi tiết đầy đủ của place sau khi user chọn từ autocomplete
        
        Args:
            place_id: ID từ autocomplete result
            fields: Các field cần lấy
            language: Ngôn ngữ
        
        Returns:
            Thông tin chi tiết: name, address, location, rating, photos, etc.
        """
        if fields is None:
            fields = [
                "place_id",
                "name", 
                "formatted_address",
                "geometry/location",
                "address_components",
                "rating",
                "opening_hours",
                "formatted_phone_number",
                "website",
                "photos",
                "types"
            ]
        
        params = {
            "place_id": place_id,
            "fields": ",".join(fields),
            "language": language,
            "key": self.api_key
        }
        
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
    
    async def get_route_with_traffic(
        self,
        origin: str,
        destination: str,
        mode: str = "driving",
        departure_time: str = "now"
    ) -> Dict[str, Any]:
        """
        Get route with traffic information (duration_in_traffic)
        
        Args:
            origin: Điểm xuất phát
            destination: Điểm đến
            mode: Phương thức di chuyển (driving, transit)
            departure_time: "now" hoặc Unix timestamp
        
        Returns:
            Route data with traffic delay information
        """
        params = {
            "origin": origin,
            "destination": destination,
            "mode": mode,
            "departure_time": departure_time,
            "key": self.api_key
        }
        
        url = f"{self.base_url}/directions/json"
        response = await self.client.get(url, params=params)
        result = response.json()
        
        if result.get("status") == "OK" and result.get("routes"):
            route = result["routes"][0]
            leg = route["legs"][0]
            
            duration_normal = leg.get("duration", {}).get("value", 0)
            duration_traffic = leg.get("duration_in_traffic", {}).get("value", duration_normal)
            traffic_delay = duration_traffic - duration_normal
            
            # Calculate traffic congestion ratio
            congestion_ratio = duration_traffic / duration_normal if duration_normal > 0 else 1.0
            
            return {
                "status": "OK",
                "route": route,
                "duration_normal_seconds": duration_normal,
                "duration_in_traffic_seconds": duration_traffic,
                "traffic_delay_seconds": traffic_delay,
                "congestion_ratio": round(congestion_ratio, 2),
                "has_traffic_data": "duration_in_traffic" in leg
            }
        
        return result
    
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

async def create_maps_client(api_key: Optional[str] = None) -> GoogleMapsAPI:
    return GoogleMapsAPI(api_key=api_key)