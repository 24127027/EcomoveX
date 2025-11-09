from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List, Dict, Any, Tuple

class Bounds(BaseModel):
    northeast: Tuple[float, float]
    southwest: Tuple[float, float]

class Geometry(BaseModel):
    location: Tuple[float, float]
    location_type: Optional[str] = None
    viewport: Optional[Bounds] = None
    bounds: Optional[Bounds] = None

class Distance(BaseModel):
    text: str
    value: int

class Duration(BaseModel):
    text: str
    value: int

class SearchSuggestion(BaseModel):
    place_id: str
    description: str
    main_text: str
    secondary_text: str
    types: List[str]
    distance_meters: Optional[int] = None

class PlacePrediction(BaseModel):
    description: str
    place_id: str
    reference: str
    structured_formatting: Optional[Dict[str, Any]] = None
    terms: Optional[List[Dict[str, str]]] = None
    types: List[str]
    matched_substrings: Optional[List[Dict[str, Any]]] = None
    distance_meters: Optional[int] = None

class AutocompleteResponse(BaseModel):
    status: str
    predictions: List[PlacePrediction] = Field(default_factory=list)
    error_message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class SearchLocationRequest(BaseModel):
    query: str = Field(..., min_length=2)
    user_location: Optional[Tuple[float, float]] = None
    radius: Optional[int] = Field(None, ge=100, le=50000)
    place_types: Optional[str] = None
    language: str = "vi"

class SearchLocationResponse(BaseModel):
    status: str
    query: str
    suggestions: List[SearchSuggestion]

class PhotoInfo(BaseModel):
    photo_reference: str
    width: int
    height: int

class OpeningHours(BaseModel):
    open_now: bool
    periods: Optional[List[Dict[str, Any]]] = None
    weekday_text: Optional[List[str]] = None

class AddressComponent(BaseModel):
    long_name: str
    short_name: str
    types: List[str]

class PlaceDetails(BaseModel):
    place_id: str
    name: str
    formatted_address: str
    geometry: Geometry
    types: List[str]
    address_components: Optional[List[AddressComponent]] = None
    formatted_phone_number: Optional[str] = None
    international_phone_number: Optional[str] = None
    opening_hours: Optional[OpeningHours] = None
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    price_level: Optional[int] = None
    website: Optional[str] = None
    photos: Optional[List[PhotoInfo]] = None
    reviews: Optional[List[Dict[str, Any]]] = None
    url: Optional[str] = None
    vicinity: Optional[str] = None
    utc_offset: Optional[int] = None

class PlaceDetailsResponse(BaseModel):
    status: str
    result: Optional[PlaceDetails] = None
    html_attributions: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class TransitVehicle(BaseModel):
    name: str
    type: str
    icon: Optional[str] = None
    local_icon: Optional[str] = None

class TransitLine(BaseModel):
    name: str
    short_name: Optional[str] = None
    color: Optional[str] = None
    vehicle: TransitVehicle
    agencies: Optional[List[Dict[str, Any]]] = None
    url: Optional[str] = None

class TransitStop(BaseModel):
    name: str
    location: Tuple[float, float]

class TransitDetails(BaseModel):
    arrival_stop: TransitStop
    departure_stop: TransitStop
    arrival_time: Dict[str, Any]
    departure_time: Dict[str, Any]
    headsign: Optional[str] = None
    headway: Optional[int] = None
    line: TransitLine
    num_stops: int

class Polyline(BaseModel):
    points: str

class Step(BaseModel):
    distance: Distance
    duration: Duration
    start_location: Tuple[float, float]
    end_location: Tuple[float, float]
    html_instructions: str
    travel_mode: str
    polyline: Optional[Polyline] = None
    transit_details: Optional[TransitDetails] = None
    steps: Optional[List['Step']] = None
    
    model_config = ConfigDict(from_attributes=True)

class Leg(BaseModel):
    distance: Distance
    duration: Duration
    start_address: str
    end_address: str
    start_location: Tuple[float, float]
    end_location: Tuple[float, float]
    steps: List[Step]
    duration_in_traffic: Optional[Duration] = None
    arrival_time: Optional[Dict[str, Any]] = None
    departure_time: Optional[Dict[str, Any]] = None

class Route(BaseModel):
    summary: str
    legs: List[Leg]
    overview_polyline: Polyline
    bounds: Bounds
    copyrights: str
    warnings: Optional[List[str]] = None
    waypoint_order: Optional[List[int]] = None
    fare: Optional[Dict[str, Any]] = None

class DirectionsResponse(BaseModel):
    status: str
    routes: List[Route] = Field(default_factory=list)
    geocoded_waypoints: Optional[List[Dict[str, Any]]] = None
    available_travel_modes: Optional[List[str]] = None
    error_message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class GeocodingResult(BaseModel):
    place_id: str
    formatted_address: str
    address_components: List[AddressComponent]
    geometry: Geometry
    types: List[str]
    plus_code: Optional[Dict[str, str]] = None
    partial_match: Optional[bool] = None

class GeocodingResponse(BaseModel):
    status: str
    results: List[GeocodingResult] = Field(default_factory=list)
    error_message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
