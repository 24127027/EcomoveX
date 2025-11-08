import httpx
import requests
from typing import Dict, Any, Optional
from utils.config import settings
from models.route import TransportMode
class climatiqAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.CLIMATIQ_API_KEY
        if not self.api_key:
            raise ValueError("CLIMATIQ_API_KEY not found in environment variables")

        self.travel_base_url = "https://preview.api.climatiq.io/travel/v1-preview3"
        self.basic_base_url = "https://api.climatiq.io/data/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(headers=self.headers, timeout=10)
        
    async def close(self):
        await self.client.aclose()

    async def estimate_travel_distance(
        self,
        mode: TransportMode,
        distance_km: float,
        passengers: int = 1,
        fuel_type: Optional[str] = None
    ) -> float:
        url = f"{self.travel_base_url}/estimate"
        payload = {
            "travel_mode": mode.value,
            "distance": distance_km,
            "distance_unit": "km",
            "passengers": passengers
        }

        if mode == TransportMode.car and fuel_type:
            payload["vehicle"] = {"fuel": fuel_type.lower()}

        try:
            res = requests.post(url, headers=self.headers, json=payload)
            res.raise_for_status()
            data = res.json()
            return data["co2e"]

        except requests.exceptions.RequestException as e:
            raise Exception(f"Travel estimation failed: {e}")
        
    async def estimate_electric_bus(self, distance_km: float = 100, passenger: int = 1) -> float:
        url = f"{self.basic_base_url}/estimate"
        params = {
            "emission_factor": {
                "activity_id": "passenger_vehicle-vehicle_type_bus-fuel_source_bev-engine_size_na-vehicle_age_na-vehicle_weight_gte_12t",
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
            return data["co2e"] * passenger / 30 # assuming average bus occupancy of 30
        except requests.exceptions.RequestException as e:
            raise Exception(f"Electric bus estimation failed: {e}")


    async def estimate_motorbike(self, distance_km: float = 100) -> float:
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
            return data["co2e"]
        except requests.exceptions.RequestException as e:
            raise Exception(f"Motorbike estimation failed: {e}")

    async def estimate_transport(
        self,
        mode: TransportMode,
        distance_km: float,
        passengers: int = 1,
        fuel_type: Optional[str] = None
    ) -> float:
        """
        Unified transport emission estimator.
        Uses the Travel API for 'car', 'rail', 'air';
        Uses Basic Estimate API for 'motorbike'.
        Returns only co2e_total and unit.
        """
        # Zero emissions for walking and bicycling
        if mode in [TransportMode.walking, TransportMode.bicycle, TransportMode.bicycling]:
            return 0.0

        travel_modes = {TransportMode.car, TransportMode.rail, TransportMode.air}

        if mode in travel_modes:
            return await self.estimate_travel_distance(mode, distance_km, passengers, fuel_type)
        elif mode == TransportMode.motorbike:
            return await self.estimate_motorbike(distance_km)
        elif mode == TransportMode.electric_bus:
            return await self.estimate_electric_bus(distance_km, passengers)
        else:
            raise ValueError(f"Unsupported travel mode: {mode.value}")

async def create_climatiq_client(api_key: Optional[str] = None):
    return climatiqAPI(api_key=api_key)