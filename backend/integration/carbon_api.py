"""
Carbon Emissions API Integration
Provides access to carbon calculation services:
- Carbon Interface API
- Custom carbon calculation formulas
- Transportation emissions estimations
"""

import httpx
from typing import Optional, Dict, Any, List
from utils.config import settings
from datetime import datetime


class CarbonInterfaceClient:
    """
    Client for Carbon Interface API.
    
    Supports:
    - Flight emissions
    - Vehicle emissions
    - Electricity emissions
    - Shipping emissions
    
    API Documentation: https://docs.carboninterface.com/
    """
    
    BASE_URL = "https://www.carboninterface.com/api/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key from settings or parameter."""
        self.api_key = api_key or settings.CARBON_INTERFACE_API_KEY
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def estimate_flight_emissions(
        self,
        passengers: int,
        departure_airport: str,
        destination_airport: str,
        cabin_class: str = "economy",
    ) -> Dict[str, Any]:
        """
        Calculate CO2 emissions for a flight.
        
        Args:
            passengers: Number of passengers
            departure_airport: IATA code (e.g., "SFO")
            destination_airport: IATA code (e.g., "JFK")
            cabin_class: "economy", "business", "first", or "premium"
        
        Returns:
            Dictionary with emission data (kg CO2)
        """
        url = f"{self.BASE_URL}/estimates"
        
        payload = {
            "type": "flight",
            "passengers": passengers,
            "legs": [
                {
                    "departure_airport": departure_airport,
                    "destination_airport": destination_airport,
                    "cabin_class": cabin_class,
                }
            ]
        }
        
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    async def estimate_vehicle_emissions(
        self,
        distance_value: float,
        distance_unit: str = "km",
        vehicle_make: Optional[str] = None,
        vehicle_model: Optional[str] = None,
        vehicle_year: Optional[int] = None,
        vehicle_model_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculate CO2 emissions for a vehicle trip.
        
        Args:
            distance_value: Distance traveled
            distance_unit: "km" or "mi"
            vehicle_make: Vehicle manufacturer (e.g., "Toyota")
            vehicle_model: Vehicle model (e.g., "Camry")
            vehicle_year: Vehicle year
            vehicle_model_id: Specific vehicle model ID from API
        
        Returns:
            Dictionary with emission data (kg CO2)
        """
        url = f"{self.BASE_URL}/estimates"
        
        payload = {
            "type": "vehicle",
            "distance_unit": distance_unit,
            "distance_value": distance_value,
        }
        
        if vehicle_model_id:
            payload["vehicle_model_id"] = vehicle_model_id
        else:
            if vehicle_make:
                payload["vehicle_make"] = vehicle_make
            if vehicle_model:
                payload["vehicle_model"] = vehicle_model
            if vehicle_year:
                payload["vehicle_year"] = vehicle_year
        
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    async def get_vehicle_makes(self) -> List[str]:
        """
        Get list of supported vehicle manufacturers.
        
        Returns:
            List of vehicle make names
        """
        url = f"{self.BASE_URL}/vehicle_makes"
        
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        return [make["data"]["attributes"]["name"] for make in data]
    
    async def get_vehicle_models(
        self,
        vehicle_make: str,
        year: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get list of vehicle models for a specific manufacturer.
        
        Args:
            vehicle_make: Manufacturer name
            year: Optional year to filter by
        
        Returns:
            List of vehicle model dictionaries
        """
        url = f"{self.BASE_URL}/vehicle_makes/{vehicle_make}/vehicle_models"
        
        params = {}
        if year:
            params["year"] = year
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()


class CustomCarbonCalculator:
    """
    Custom carbon footprint calculator using standard emission factors.
    Useful when external API is unavailable or for custom calculations.
    
    Emission factors are approximate averages.
    """
    
    # Emission factors in kg CO2 per unit
    EMISSION_FACTORS = {
        # Transportation (kg CO2 per km per passenger)
        "car_gasoline": 0.192,
        "car_diesel": 0.171,
        "car_hybrid": 0.109,
        "car_electric": 0.053,
        "bus": 0.089,
        "train": 0.041,
        "metro": 0.033,
        "bicycle": 0.0,
        "walking": 0.0,
        "motorcycle": 0.113,
        "scooter_electric": 0.008,
        
        # Air travel (kg CO2 per km per passenger)
        "flight_short_haul": 0.255,  # < 1500 km
        "flight_medium_haul": 0.195,  # 1500-3500 km
        "flight_long_haul": 0.147,    # > 3500 km
        "flight_economy": 0.195,
        "flight_business": 0.390,      # 2x economy
        "flight_first": 0.585,          # 3x economy
    }
    
    @staticmethod
    def calculate_transport_emissions(
        transport_mode: str,
        distance_km: float,
        passengers: int = 1,
    ) -> float:
        """
        Calculate CO2 emissions for a transportation journey.
        
        Args:
            transport_mode: Type of transport (see EMISSION_FACTORS keys)
            distance_km: Distance in kilometers
            passengers: Number of passengers (default 1)
        
        Returns:
            CO2 emissions in kg
        """
        emission_factor = CustomCarbonCalculator.EMISSION_FACTORS.get(
            transport_mode.lower(),
            0.15  # Default average if not found
        )
        
        total_emissions = emission_factor * distance_km * passengers
        return round(total_emissions, 2)
    
    @staticmethod
    def calculate_flight_emissions(
        distance_km: float,
        cabin_class: str = "economy",
        passengers: int = 1,
    ) -> float:
        """
        Calculate flight emissions based on distance and cabin class.
        
        Args:
            distance_km: Flight distance in kilometers
            cabin_class: "economy", "business", or "first"
            passengers: Number of passengers
        
        Returns:
            CO2 emissions in kg
        """
        # Determine haul type based on distance
        if distance_km < 1500:
            base_factor = CustomCarbonCalculator.EMISSION_FACTORS["flight_short_haul"]
        elif distance_km < 3500:
            base_factor = CustomCarbonCalculator.EMISSION_FACTORS["flight_medium_haul"]
        else:
            base_factor = CustomCarbonCalculator.EMISSION_FACTORS["flight_long_haul"]
        
        # Adjust for cabin class
        multiplier = 1.0
        if cabin_class.lower() == "business":
            multiplier = 2.0
        elif cabin_class.lower() == "first":
            multiplier = 3.0
        
        total_emissions = base_factor * multiplier * distance_km * passengers
        return round(total_emissions, 2)
    
    @staticmethod
    def calculate_hotel_emissions(
        nights: int,
        hotel_type: str = "standard",
    ) -> float:
        """
        Estimate hotel stay emissions.
        
        Args:
            nights: Number of nights
            hotel_type: "budget", "standard", "luxury"
        
        Returns:
            CO2 emissions in kg
        """
        # Emission factors per night (kg CO2)
        hotel_factors = {
            "budget": 15.0,
            "standard": 30.0,
            "luxury": 50.0,
        }
        
        factor = hotel_factors.get(hotel_type.lower(), 30.0)
        return round(factor * nights, 2)
    
    @staticmethod
    def compare_transport_options(
        distance_km: float,
        transport_modes: List[str],
    ) -> Dict[str, float]:
        """
        Compare emissions across different transport modes.
        
        Args:
            distance_km: Journey distance
            transport_modes: List of transport modes to compare
        
        Returns:
            Dictionary mapping transport mode to emissions (kg CO2)
        """
        results = {}
        for mode in transport_modes:
            emissions = CustomCarbonCalculator.calculate_transport_emissions(
                mode, distance_km
            )
            results[mode] = emissions
        
        return results
    
    @staticmethod
    def get_eco_score(emissions_kg: float) -> Dict[str, Any]:
        """
        Calculate an eco-friendliness score based on emissions.
        
        Args:
            emissions_kg: Total CO2 emissions in kg
        
        Returns:
            Dictionary with score (0-100), rating, and recommendations
        """
        # Score calculation (inverse relationship with emissions)
        # Lower emissions = higher score
        if emissions_kg == 0:
            score = 100
            rating = "Excellent"
        elif emissions_kg < 10:
            score = 90
            rating = "Very Good"
        elif emissions_kg < 50:
            score = 70
            rating = "Good"
        elif emissions_kg < 100:
            score = 50
            rating = "Fair"
        elif emissions_kg < 200:
            score = 30
            rating = "Poor"
        else:
            score = 10
            rating = "Very Poor"
        
        # Generate recommendations
        recommendations = []
        if emissions_kg > 50:
            recommendations.append("Consider using public transportation")
        if emissions_kg > 100:
            recommendations.append("Look into train travel as an alternative to flying")
        if emissions_kg > 200:
            recommendations.append("Consider carbon offset programs")
        if emissions_kg > 0:
            recommendations.append("Choose eco-friendly accommodations")
        
        return {
            "score": score,
            "rating": rating,
            "emissions_kg": emissions_kg,
            "recommendations": recommendations,
            "calculated_at": datetime.utcnow().isoformat(),
        }


# Singleton instance
_carbon_client_instance: Optional[CarbonInterfaceClient] = None
_custom_calculator_instance: Optional[CustomCarbonCalculator] = None


async def get_carbon_client() -> CarbonInterfaceClient:
    """Get or create a singleton CarbonInterfaceClient."""
    global _carbon_client_instance
    if _carbon_client_instance is None:
        _carbon_client_instance = CarbonInterfaceClient()
    return _carbon_client_instance


def get_custom_calculator() -> CustomCarbonCalculator:
    """Get or create a singleton CustomCarbonCalculator."""
    global _custom_calculator_instance
    if _custom_calculator_instance is None:
        _custom_calculator_instance = CustomCarbonCalculator()
    return _custom_calculator_instance
