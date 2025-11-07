from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from enum import Enum

class TravelMode(str, Enum):
    driving = "driving"
    walking = "walking"
    bicycling = "bicycling"
    transit = "transit"

class RouteRequest(BaseModel):
    origin: str = Field(..., min_length=1, max_length=500, description="Starting location (address or coordinates)")
    destination: str = Field(..., min_length=1, max_length=500, description="Destination location (address or coordinates)")
    max_time_ratio: Optional[float] = Field(1.3, gt=0, le=5.0, description="Maximum acceptable time ratio compared to fastest route")
    language: Optional[str] = Field("vi", min_length=2, max_length=10, description="Language for route instructions")
    
    @field_validator('origin', 'destination')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Location cannot be empty or whitespace")
        return v.strip()

class CompareRoutesRequest(BaseModel):
    origin: str = Field(..., min_length=1, max_length=500, description="Starting location")
    destination: str = Field(..., min_length=1, max_length=500, description="Destination location")
    max_time_ratio: Optional[float] = Field(1.5, gt=0, le=5.0, description="Maximum acceptable time ratio")
    
    @field_validator('origin', 'destination')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Location cannot be empty or whitespace")
        return v.strip()

class EcoRouteRequest(BaseModel):
    origin: str = Field(..., min_length=1, max_length=500, description="Starting location")
    destination: str = Field(..., min_length=1, max_length=500, description="Destination location")
    avoid_highways: Optional[bool] = Field(True, description="Avoid highways for eco-friendly route")
    avoid_tolls: Optional[bool] = Field(True, description="Avoid toll roads")
    
    @field_validator('origin', 'destination')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Location cannot be empty or whitespace")
        return v.strip()

class TransitStep(BaseModel):
    line: str
    vehicle: str
    departure_stop: str
    arrival_stop: str
    num_stops: int
    duration: str

class WalkingStep(BaseModel):
    distance: str
    duration: str
    instruction: str

class TransitInfo(BaseModel):
    transit_steps: List[TransitStep]
    walking_steps: List[WalkingStep]
    total_transit_steps: int
    total_walking_steps: int

class CarbonData(BaseModel):
    co2_grams: float
    co2_kg: float
    emission_factor_g_per_km: float
    distance_km: float
    mode: str
    emission_mode: str
    data_source: str

class TimeComparison(BaseModel):
    vs_fastest_min: float
    vs_fastest_percent: float

class CarbonComparison(BaseModel):
    vs_driving_kg: float
    vs_driving_percent: float

class RouteData(BaseModel):
    type: str
    mode: str
    display_name: str
    distance_km: float
    duration_min: float
    duration_text: str
    carbon_kg: float
    carbon_grams: float
    emission_factor: float
    priority_score: float
    reason: str
    transit_info: Optional[TransitInfo] = None
    time_comparison: Optional[TimeComparison] = None
    carbon_comparison: Optional[CarbonComparison] = None
    route_details: Optional[Dict[str, Any]] = None

class Recommendation(BaseModel):
    route: str
    reason: str

class OptimalRoutesResponse(BaseModel):
    origin: str
    destination: str
    routes: Dict[str, RouteData]
    recommendation: Recommendation
    status: str
    total_routes_analyzed: int

class RouteOption(BaseModel):
    type: str
    mode: str
    mode_display: str
    distance_km: float
    duration_minutes: float
    duration_text: str
    carbon_emission: CarbonData
    is_fastest: bool
    eco_score: int
    health_benefit: Optional[str] = None
    transit_details: Optional[TransitInfo] = None
    carbon_saving_kg: Optional[float] = None
    carbon_saving_percent: Optional[float] = None
    is_recommended: Optional[bool] = None
    highlight: Optional[str] = None

class RouteSummary(BaseModel):
    origin: str
    destination: str
    total_options: int

class CompareRoutesResponse(BaseModel):
    summary: RouteSummary
    fastest_route: RouteOption
    lowest_carbon_route: RouteOption
    smart_route: Optional[RouteOption] = None
    all_options: List[RouteOption]

class EcoMetrics(BaseModel):
    estimated_co2_kg: float
    distance_km: float
    emission_factor: float

class EcoRouteResponse(BaseModel):
    status: str
    routes: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
