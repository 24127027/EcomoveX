from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from models.route import TransportMode, RouteType

class RouteCreate(BaseModel):
    user_id: int
    origin_id: int
    destination_id: str
    distance_km: float = Field(..., ge=0)
    estimated_travel_time_min: float = Field(..., ge=0)
    carbon_emission_kg: float = Field(..., ge=0)

class RouteUpdate(BaseModel):
    distance_km: Optional[float] = Field(None, ge=0)
    estimated_travel_time_min: Optional[float] = Field(None, ge=0)
    carbon_emission_kg: Optional[float] = Field(None, ge=0)

class RouteResponse(BaseModel):
    user_id: int
    origin_id: int
    destination_id: str
    distance_km: float
    estimated_travel_time_min: float
    carbon_emission_kg: float
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class TransitStep(BaseModel):
    line: str
    vehicle: TransportMode
    departure_stop: Dict[str, float]
    arrival_stop: Dict[str, float]
    num_stops: int
    duration: float

class WalkingStep(BaseModel):
    distance: float
    duration: float
    instruction: str

class TransitDetails(BaseModel):
    transit_steps: List[TransitStep]
    walking_steps: List[WalkingStep]
    total_transit_steps: int
    total_walking_steps: int

class RouteData(BaseModel):
    type: str
    mode: List[TransportMode]
    distance: float
    duration: float
    carbon: float
    route_details: Dict[str, Any]
    transit_info: Optional[TransitDetails] = None

class FindRoutesRequest(BaseModel):
    origin: Tuple[float, float]
    destination: Tuple[float, float]
    max_time_ratio: float = Field(1.3, ge=1.0, le=3.0)
    language: str = "vi"

class FindRoutesResponse(BaseModel):
    origin: Dict[str, float]
    destination: Dict[str, float]
    routes: Dict[RouteType, RouteData]
    recommendation: str
    
    model_config = ConfigDict(from_attributes=True,)
    
class RecommendResponse(BaseModel):
    route: str
    recommendation: str
    
    model_config = ConfigDict(from_attributes=True,)