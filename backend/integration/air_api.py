from schemas.air_schema import *
from utils.config import settings
from typing import Tuple, Optional, List
import httpx

class AirQualityAPI:
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.client = httpx.AsyncClient()
        self.base_url = "https://airquality.googleapis.com/v1/currentConditions:lookup"

    async def get_air_quality(
        self,
        location: Tuple[float, float],
        extra_computations: Optional[List[str]] = ["HEALTH_RECOMMENDATIONS"],
        language_code: str = "vi"
    ) -> AirQualityResponse:
        try:
            payload = {
                "location": {
                    "latitude": location[0],
                    "longitude": location[1]
                },
                "languageCode": language_code
            }
            
            if extra_computations:
                payload["extraComputations"] = extra_computations
            
            response = await self.client.post(
                self.base_url,
                params={"key": self.api_key},
                json=payload
            )
            data = response.json()
            
            if data.get("status") != "OK":
                raise ValueError(f"Error fetching air quality data: {data.get('status')}")
            
            indexes = data.get("indexes", [])
            if not indexes:
                raise ValueError("No air quality index data available")
            
            primary_index = indexes[0]
            
            return AirQualityResponse(
                location=location,
                aqi_data=AirQualityIndex(
                    display_name=primary_index.get("displayName", "Air Quality Index"),
                    aqi=primary_index.get("aqi"),
                    category=primary_index.get("category")
                ),
                recommendations=HealthRecommendation(
                    general_population=data.get("healthRecommendations", {}).get("generalPopulation"),
                    sensitive_groups=data.get("healthRecommendations", {}).get("sensitiveGroups")
                ) if data.get("healthRecommendations") else None
            )
        except Exception as e:
            print(f"Error in get_air_quality: {e}")
            raise e