from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from enum import Enum
from schemas.destination_schema import Location
from schemas.map_schema import Bounds

class TransportMode(str, Enum):
    car = "car"
    motorbike = "motorbike"
    walking = "walking"
    metro = "metro"
    bus = "bus"
    train = "train"
        
class RouteType(str, Enum):
    fastest = "fastest"
    low_carbon = "low_carbon"
    smart_combination = "smart_combination"

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
    origin: Location
    destination: Location
    max_time_ratio: float = Field(1.3, ge=1.0, le=3.0)
    language: str = "vi"

class FindRoutesResponse(BaseModel):
    origin: Dict[str, float]
    destination: Dict[str, float]
    routes: Dict[RouteType, RouteData]
    recommendation: str
    
    model_config = ConfigDict(from_attributes=True)
    
class RecommendResponse(BaseModel):
    route: str
    recommendation: str
    
    model_config = ConfigDict(from_attributes=True)
    
class TransitDetails(BaseModel):
    arrival_stop: Tuple[str, Location]
    departure_stop: Tuple[str, Location]
    arrival_time: Dict[str, Any]
    departure_time: Dict[str, Any]
    headway: Optional[int] = None
    line: str

class Step(BaseModel):
    distance: float  # in kilometers
    duration: float  # in minutes
    start_location: Location
    end_location: Location
    html_instructions: str
    travel_mode: TransportMode
    polyline: Optional[str] = None
    transit_details: Optional[TransitDetails] = None

    model_config = ConfigDict(from_attributes=True)

class Leg(BaseModel):
    distance: float  # in kilometers
    duration: float  # in minutes
    start_location: Tuple[str, Location]
    end_location: Tuple[str, Location]
    steps: List[Step]
    duration_in_traffic: Optional[float] = None
    arrival_time: Optional[Dict[str, Any]] = None
    departure_time: Optional[Dict[str, Any]] = None

class Route(BaseModel):
    summary: str
    legs: List[Leg]
    overview_polyline: str
    bounds: Bounds
    distance: float  # in kilometers (sum of all legs)
    duration: float  # in minutes (sum of all legs)
    duration_in_traffic: Optional[float] = None

class DirectionsRequest(BaseModel):
    origin: Location
    destination: Location
    waypoints: Optional[List[Location]] = None
    alternatives: bool = False
    avoid: Optional[List[str]] = None
    get_traffic: bool = False

class DirectionsResponse(BaseModel):
    routes: List[Route] = Field(default_factory=list)
    travel_mode: Optional[TransportMode] = None
    
    model_config = ConfigDict(from_attributes=True)
