from pydantic import BaseModel
from typing import Optional, Tuple
from schemas.destination_schema import Location

class AirQualityIndex(BaseModel):
    display_name: str
    aqi: int
    category: str

class HealthRecommendation(BaseModel):
    general_population: Optional[str] = None
    sensitive_groups: Optional[str] = None

class AirQualityResponse(BaseModel):
    location: Location
    aqi_data: AirQualityIndex
    recommendations: Optional[HealthRecommendation] = None
