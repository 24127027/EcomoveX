from typing import Optional

import httpx
import requests

from schemas.route_schema import *
from utils.config import settings


class CarbonAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.CLIMATIQ_API_KEY
        if not self.api_key:
            raise ValueError("CLIMATIQ_API_KEY not found in environment variables")

        self.travel_base_url = "https://preview.api.carbonAPI.io/travel/v1-preview3"
        self.basic_base_url = "https://api.carbonAPI.io/data/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(headers=self.headers, timeout=10)

    async def close(self):
        await self.client.aclose()

    async def estimate_car(
        self,
        distance_km: float,
        passengers: int = 1,
    ) -> float:
        url = f"{self.basic_base_url}/estimate"
        activity_id = "passenger_vehicle-vehicle_type_car-fuel_source_na-engine_size_na-vehicle_age_na-vehicle_weight_na"
        params = {
            "emission_factor": {"activity_id": activity_id, "data_version": "^27"},
            "parameters": {"distance": distance_km, "distance_unit": "km"},
        }

        try:
            res = requests.post(url, headers=self.headers, json=params)

            if res.status_code != 200:
                raise ValueError(f"Error estimating car emissions: HTTP {res.status_code}")

            data = res.json()
            if "error" in data:
                raise ValueError(f"Error in car emissions response: {data.get('error')}")

            return data["co2e"] / passengers if passengers > 1 else data["co2e"]

        except requests.exceptions.RequestException as e:
            raise Exception(f"Car estimation failed: {e}")

    async def estimate_electric_bus(self, distance_km: float = 100, passenger: int = 1) -> float:
        url = f"{self.basic_base_url}/estimate"
        params = {
            "emission_factor": {
                "activity_id": (
                    "passenger_vehicle-vehicle_type_bus-fuel_source_bev-engine_size_na-vehicle_age_na-vehicle_weight_gte_12t"
                ),
                "data_version": "^27",
            },
            "parameters": {"distance": distance_km, "distance_unit": "km"},
        }
        try:
            response = requests.post(url, headers=self.headers, json=params)

            if response.status_code != 200:
                raise ValueError(
                    f"Error estimating electric bus emissions: HTTP {response.status_code}"
                )

            data = response.json()
            if "error" in data:
                raise ValueError(f"Error in electric bus emissions response: {data.get('error')}")

            return data["co2e"] * passenger / 30
        except requests.exceptions.RequestException as e:
            raise Exception(f"Electric bus estimation failed: {e}")

    async def estimate_motorbike(self, distance_km: float = 100) -> float:
        url = f"{self.basic_base_url}/estimate"
        params = {
            "emission_factor": {
                "activity_id": (
                    "passenger_vehicle-vehicle_type_motorbike-fuel_source_na-engine_size_na-vehicle_age_na-vehicle_weight_na"
                ),
                "data_version": "^27",
            },
            "parameters": {"distance": distance_km, "distance_unit": "km"},
        }

        try:
            response = requests.post(url, headers=self.headers, json=params)

            if response.status_code != 200:
                raise ValueError(
                    f"Error estimating motorbike emissions: HTTP {response.status_code}"
                )

            data = response.json()
            if "error" in data:
                raise ValueError(f"Error in motorbike emissions response: {data.get('error')}")

            return data["co2e"]
        except requests.exceptions.RequestException as e:
            raise Exception(f"Motorbike estimation failed: {e}")

    async def estimate_transport(
        self,
        mode: TransportMode,
        distance_km: float,
        passengers: int = 1,
    ) -> float:

        if mode == TransportMode.walking:
            return 0.0

        if mode == TransportMode.car:
            return await self.estimate_car(distance_km, passengers)
        elif mode == TransportMode.motorbike:
            return await self.estimate_motorbike(distance_km)
        elif mode == TransportMode.bus:
            return await self.estimate_electric_bus(distance_km, passengers)
        else:
            raise ValueError(f"Unsupported travel mode: {mode.value}")


async def create_carbonAPI_client(api_key: Optional[str] = None):
    return CarbonAPI(api_key=api_key)
