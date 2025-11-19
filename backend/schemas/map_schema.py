from pydantic import BaseModel, Field, validator, field_validator, ConfigDict
from typing import Optional, List, Dict, Any, Tuple, Union
from models.route import *

class Bounds(BaseModel):
    northeast: Tuple[float, float]
    southwest: Tuple[float, float]

class Geometry(BaseModel):
    location: Tuple[float, float]
    bounds: Optional[Bounds] = None

class PlaceSearchDisplay(BaseModel):
    description: str
    place_id: str
    structured_formatting: Optional[Dict[str, Any]] = None
    types: List[str]
    matched_substrings: Optional[List[Dict[str, Any]]] = None
    distance: Optional[float] = None

class AutocompleteResponse(BaseModel):
    predictions: List[PlaceSearchDisplay] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)

class SearchLocationRequest(BaseModel):
    query: str = Field(..., min_length=2)
    user_location: Optional[Tuple[float, float]] = None
    radius: Optional[int] = Field(None, ge=100, le=50000)
    place_types: Optional[str] = None
    language: str = "vi"

class PhotoInfo(BaseModel):
    photo_reference: str
    size: Tuple[int, int]

class OpeningHours(BaseModel):
    open_now: bool
    periods: Optional[List[Dict[str, Any]]] = None
    weekday_text: Optional[List[str]] = None

class AddressComponent(BaseModel):
    name: str
    types: List[str]
    
class Review(BaseModel):
    rating: float
    text: str

class PlaceDetailsResponse(BaseModel):
    place_id: str
    name: str
    formatted_address: str
    address_components: Optional[List[AddressComponent]] = None
    formatted_phone_number: Optional[str] = None
    geometry: Geometry
    types: List[str]
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    price_level: Optional[int] = None
    opening_hours: Optional[OpeningHours] = None
    website: Optional[str] = None
    photos: Optional[List[PhotoInfo]] = None
    reviews: Optional[List[Review]] = None
    utc_offset: Optional[int] = None
    sustainable_certified: bool = False

class TransitDetails(BaseModel):
    arrival_stop: Tuple[str, Tuple[float, float]]
    departure_stop: Tuple[str, Tuple[float, float]]
    arrival_time: Dict[str, Any]
    departure_time: Dict[str, Any]
    headway: Optional[int] = None
    line: str

class Step(BaseModel):
    distance: float  # in kilometers
    duration: float  # in minutes
    start_location: Tuple[float, float]
    end_location: Tuple[float, float]
    html_instructions: str
    travel_mode: TransportMode
    polyline: Optional[str] = None
    transit_details: Optional[TransitDetails] = None

    model_config = ConfigDict(from_attributes=True)

class Leg(BaseModel):
    distance: float  # in kilometers
    duration: float  # in minutes
    start_location: Tuple[str, Tuple[float, float]]
    end_location: Tuple[str, Tuple[float, float]]
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
    origin: Tuple[float, float]
    destination: Tuple[float, float]
    waypoints: Optional[List[Tuple[float, float]]] = None
    alternatives: bool = False
    avoid: Optional[List[str]] = None
    get_traffic: bool = False

class DirectionsResponse(BaseModel):
    routes: List[Route] = Field(default_factory=list)
    available_travel_modes: Optional[TransportMode] = None
    
    model_config = ConfigDict(from_attributes=True)

class GeocodingResult(BaseModel):
    place_id: str
    formatted_address: str
    address_components: List[AddressComponent]
    geometry: Geometry
    types: List[str]

class GeocodingResponse(BaseModel):
    results: List[GeocodingResult] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)

class AirQualityIndex(BaseModel):
    display_name: str
    aqi: int
    category: str

class HealthRecommendation(BaseModel):
    general_population: Optional[str] = None
    sensitive_groups: Optional[str] = None

class AirQualityResponse(BaseModel):
    location: Tuple[float, float]
    aqi_data: AirQualityIndex
    recommendations: Optional[HealthRecommendation] = None
        
class NearbyPlaceRequest(BaseModel):
    location: Tuple[float, float]
    radius: Optional[int]
    rank_by: str = "prominence"
    place_type: Optional[str] = None
    keyword: Optional[str] = None

class NearbyPlaceSimple(BaseModel):
    place_id: str
    name: str
    location: Tuple[float, float]
    rating: Optional[float] = None
    types: List[str]

class NearbyPlacesResponse(BaseModel):
    center: Tuple[float, float]
    places: List[NearbyPlaceSimple]
    next_page_token: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class RouteComparisonMode(BaseModel):
    mode: TransportMode
    distance: Optional[float] = None
    duration: Optional[float] = None
    carbon_kg: Optional[float] = None
    polyline: Optional[str] = None
    bounds: Optional[Bounds] = None

class RouteComparisonResponse(BaseModel):
    origin: Tuple[float, float]
    destination: Tuple[float, float]
    routes: Dict[str, RouteComparisonMode]

class SearchAlongRouteResponse(BaseModel):
    route_polyline: str
    places_along_route: List[NearbyPlaceSimple]
    search_type: str