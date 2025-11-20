from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Tuple

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

class GeocodingResult(BaseModel):
    place_id: str
    formatted_address: str
    address_components: List[AddressComponent]
    geometry: Geometry
    types: List[str]

class GeocodingResponse(BaseModel):
    results: List[GeocodingResult] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)
        
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

class SearchAlongRouteResponse(BaseModel):
    route_polyline: str
    places_along_route: List[NearbyPlaceSimple]
    search_type: str