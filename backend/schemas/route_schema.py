from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from schemas.destination_schema import Bounds, Location


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
    plan_id: int
    origin_plan_destination_id: int
    destination_plan_destination_id: int
    distance_km: float = Field(..., ge=0)
    carbon_emission_kg: float = Field(..., ge=0)
    mode: TransportMode


class RouteResponse(BaseModel):
    id: int
    plan_id: int
    origin_plan_destination_id: int
    destination_plan_destination_id: int
    distance_km: float
    carbon_emission_kg: float
    mode: TransportMode

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
    origin: Location
    destination: Location
    routes: Dict[RouteType, RouteData]
    recommendation: str

    model_config = ConfigDict(from_attributes=True)


class RecommendResponse(BaseModel):
    route: str
    recommendation: str

    model_config = ConfigDict(from_attributes=True)


class TransitStepDetail(BaseModel):
    arrival_stop: Tuple[str, Location]
    departure_stop: Tuple[str, Location]
    arrival_time: Dict[str, Any]
    departure_time: Dict[str, Any]
    headway: Optional[str] = None  # Changed from int to str (headsign from v1 API)
    line: str


class Step(BaseModel):
    distance: float  # in kilometers
    duration: float  # in minutes
    start_location: Location
    end_location: Location
    html_instructions: str
    travel_mode: TransportMode
    polyline: Optional[str] = None
    transit_details: Optional[TransitStepDetail] = None

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


class TripMetricsResponse(BaseModel):
    total_distance_km: float = Field(default=0.0)
    total_duration_min: float = Field(default=0.0)
    details: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
    
    
class RouteForPlanResponse(BaseModel):
    origin: str # place_id
    destination: str # place_id
    distance_km: float
    estimated_travel_time_min: float
    carbon_emission_kg: float
    route_polyline: str
    transport_mode: TransportMode = TransportMode.car
    route_type: RouteType = RouteType.fastest

    model_config = ConfigDict(from_attributes=True)