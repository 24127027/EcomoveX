import os
import requests
from typing import Dict, Any, Optional
from utils.config import settings

class climatiqAPI:
    """
    A class to estimate carbon emissions for transport using the Climatiq API.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the estimator with Climatiq API credentials.
        """
        self.api_key = api_key or settings.CLIMATIQ_API_KEY
        if not self.api_key:
            raise ValueError("CLIMATIQ_API_KEY not found in environment variables")

        self.travel_base_url = "https://preview.api.climatiq.io/travel/v1-preview3"
        self.basic_base_url = "https://api.climatiq.io/data/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def estimate_travel_distance(
        self,
        mode: str,
        distance_km: float,
        passengers: int = 1,
        fuel_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Estimate emissions using the Travel API with a known distance.
        Returns only co2e_total and unit.
        """
        url = f"{self.travel_base_url}/estimate"
        payload = {
            "travel_mode": mode,
            "distance": distance_km,
            "distance_unit": "km",
            "passengers": passengers
        }

        # Include fuel type only if supported (car mode)
        if mode == "car" and fuel_type:
            payload["vehicle"] = {"fuel": fuel_type.lower()}  # e.g., "petrol", "diesel", "electric"

        try:
            res = requests.post(url, headers=self.headers, json=payload)
            res.raise_for_status()
            data = res.json()
            return {
                "co2e_total": data["co2e"],
                "unit": data["co2e_unit"]
            }
        except requests.exceptions.RequestException as e:
            raise Exception(f"Travel estimation failed: {e}")

    async def estimate_motorbike(self, distance_km: float = 100) -> Dict[str, Any]:
        """
        Estimate emissions for motorbike using Basic Estimate API.
        Returns only co2e_total and unit.
        """
        url = f"{self.basic_base_url}/estimate"
        params = {
            "emission_factor": {
                "activity_id": "passenger_vehicle-vehicle_type_motorbike-fuel_source_na-engine_size_na-vehicle_age_na-vehicle_weight_na",
                "data_version": "^27"
            },
            "parameters": {
                "distance": distance_km,
                "distance_unit": "km"
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=params)
            response.raise_for_status()
            data = response.json()
            return {
                "co2e_total": data["co2e"],
                "unit": data["co2e_unit"]
            }
        except requests.exceptions.RequestException as e:
            raise Exception(f"Motorbike estimation failed: {e}")

    async def estimate_transport(
        self,
        mode: str,
        distance_km: float,
        passengers: int = 1,
        fuel_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Unified transport emission estimator.
        Uses the Travel API for 'car', 'rail', 'air';
        Uses Basic Estimate API for 'motorbike'.
        Returns only co2e_total and unit.
        """
        travel_modes = {"car", "rail", "air"}

        if mode in travel_modes:
            return self.estimate_travel_distance(mode, distance_km, passengers, fuel_type)
        elif mode == "motorbike":
            return self.estimate_motorbike(distance_km)
        else:
            raise ValueError(f"Unsupported travel mode: {mode}")

