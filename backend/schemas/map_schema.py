from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List, Dict, Any, Tuple

class Bounds(BaseModel):
    """Geographical bounds (northeast and southwest corners)"""
    northeast: Tuple[float, float]
    southwest: Tuple[float, float]

class Geometry(BaseModel):
    """Location geometry information"""
    location: Tuple[float, float]
    location_type: Optional[str] = None
    viewport: Optional[Bounds] = None
    bounds: Optional[Bounds] = None

class Distance(BaseModel):
    """Distance information"""
    text: str = Field(..., description="Human-readable distance (e.g., '1.5 km')")
    value: int = Field(..., description="Distance in meters")

class Duration(BaseModel):
    """Duration information"""
    text: str = Field(..., description="Human-readable duration (e.g., '5 mins')")
    value: int = Field(..., description="Duration in seconds")

class SearchSuggestion(BaseModel):
    place_id: str = Field(..., description="Google Place ID")
    description: str = Field(..., description="Mô tả đầy đủ")
    main_text: str = Field(..., description="Text chính (tên địa điểm)")
    secondary_text: str = Field(..., description="Text phụ (địa chỉ)")
    types: List[str] = Field(..., description="Các loại địa điểm")
    distance_meters: Optional[int] = Field(None, description="Khoảng cách từ user location")

class PlacePrediction(BaseModel):
    """Place autocomplete prediction"""
    description: str = Field(..., description="Full description of the place")
    place_id: str
    reference: str
    structured_formatting: Optional[Dict[str, Any]] = None
    terms: Optional[List[Dict[str, str]]] = None
    types: List[str]
    matched_substrings: Optional[List[Dict[str, Any]]] = None
    distance_meters: Optional[int] = None

class AutocompleteResponse(BaseModel):
    """Google Maps Places Autocomplete API response"""
    status: str = Field(..., description="OK, ZERO_RESULTS, etc.")
    predictions: List[PlacePrediction] = Field(default_factory=list)
    error_message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class SearchLocationRequest(BaseModel):
    """Request cho search_location"""
    query: str = Field(..., min_length=2, description="Text search")
    user_location: Optional[Tuple[float, float]] = Field(None, description="Tọa độ user (lat, lng)")
    radius: Optional[int] = Field(None, ge=100, le=50000, description="Bán kính (100-50000m)")
    place_types: Optional[str] = Field(None, description="Loại địa điểm")
    language: str = Field("vi", description="Ngôn ngữ")

    @validator('user_location')
    def validate_location_pair(cls, user_location):
        if user_location is not None:
            lat, lng = user_location
            if lat is None or lng is None:
                raise ValueError("user_location phải có cả lat và lng")
        return user_location

class SearchLocationResponse(BaseModel):
    status: str = Field(..., description="Status: OK")
    query: str = Field(..., description="Query gốc")
    suggestions: List[SearchSuggestion] = Field(..., description="List suggestions")

class PhotoInfo(BaseModel):
    """Simplified photo info for Vietnamese API"""
    photo_reference: str = Field(..., description="Reference để get photo")
    width: int = Field(..., description="Chiều rộng")
    height: int = Field(..., description="Chiều cao")

class OpeningHours(BaseModel):
    """Place opening hours"""
    open_now: bool
    periods: Optional[List[Dict[str, Any]]] = None
    weekday_text: Optional[List[str]] = None

class AddressComponent(BaseModel):
    """Component of a structured address"""
    long_name: str
    short_name: str
    types: List[str]

class PlaceDetails(BaseModel):
    """Detailed place information"""
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
    """Google Maps Place Details API response"""
    status: str = Field(..., description="OK, NOT_FOUND, etc.")
    result: Optional[PlaceDetails] = None
    html_attributions: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class TransitVehicle(BaseModel):
    """Transit vehicle information"""
    name: str = Field(..., description="Vehicle name (e.g., 'Bus', 'Subway')")
    type: str = Field(..., description="Vehicle type (BUS, SUBWAY, TRAIN, etc.)")
    icon: Optional[str] = None
    local_icon: Optional[str] = None

class TransitLine(BaseModel):
    """Transit line information"""
    name: str = Field(..., description="Line name")
    short_name: Optional[str] = Field(None, description="Short name (e.g., '86', 'Line 2A')")
    color: Optional[str] = None
    vehicle: TransitVehicle
    agencies: Optional[List[Dict[str, Any]]] = None
    url: Optional[str] = None

class TransitStop(BaseModel):
    """Transit stop information"""
    name: str = Field(..., description="Stop name")
    location: Tuple[float, float] = Field(..., description="Stop coordinates")

class TransitDetails(BaseModel):
    """Detailed transit information for a step"""
    arrival_stop: TransitStop
    departure_stop: TransitStop
    arrival_time: Dict[str, Any]
    departure_time: Dict[str, Any]
    headsign: Optional[str] = None
    headway: Optional[int] = None
    line: TransitLine
    num_stops: int = Field(..., description="Number of stops")

class Polyline(BaseModel):
    """Encoded polyline for route visualization"""
    points: str = Field(..., description="Encoded polyline string")

class Step(BaseModel):
    """A step in a leg of a route"""
    distance: Distance
    duration: Duration
    start_location: Tuple[float, float]
    end_location: Tuple[float, float]
    html_instructions: str = Field(..., description="HTML formatted instructions")
    travel_mode: str = Field(..., description="DRIVING, WALKING, BICYCLING, TRANSIT")
    polyline: Optional[Polyline] = None
    transit_details: Optional[TransitDetails] = None
    steps: Optional[List['Step']] = None  # For sub-steps in transit
    
    model_config = ConfigDict(from_attributes=True)

class Leg(BaseModel):
    """A leg of a route (between two waypoints)"""
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
    """A route with one or more legs"""
    summary: str = Field(..., description="Short summary of route")
    legs: List[Leg]
    overview_polyline: Polyline
    bounds: Bounds
    copyrights: str
    warnings: Optional[List[str]] = None
    waypoint_order: Optional[List[int]] = None
    fare: Optional[Dict[str, Any]] = None

class DirectionsResponse(BaseModel):
    """Google Maps Directions API response"""
    status: str = Field(..., description="OK, NOT_FOUND, ZERO_RESULTS, etc.")
    routes: List[Route] = Field(default_factory=list)
    geocoded_waypoints: Optional[List[Dict[str, Any]]] = None
    available_travel_modes: Optional[List[str]] = None
    error_message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class GeocodingResult(BaseModel):
    """A single geocoding result"""
    place_id: str
    formatted_address: str
    address_components: List[AddressComponent]
    geometry: Geometry
    types: List[str]
    plus_code: Optional[Dict[str, str]] = None
    partial_match: Optional[bool] = None

class GeocodingResponse(BaseModel):
    """Google Maps Geocoding API response"""
    status: str = Field(..., description="OK, ZERO_RESULTS, etc.")
    results: List[GeocodingResult] = Field(default_factory=list)
    error_message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)