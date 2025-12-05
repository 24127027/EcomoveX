from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from schemas.destination_schema import Bounds


class Location(BaseModel):
    longitude: float = Field(alias="lng")
    latitude: float = Field(alias="lat")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        ser_json_tuples=False,
        json_schema_extra={"serialization": {"by_alias": True}},
    )


class Geometry(BaseModel):
    location: Location
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


class AutocompleteRequest(BaseModel):
    query: str = Field(..., min_length=2)
    user_location: Optional[Location] = None
    radius: Optional[int] = Field(None, ge=100, le=50000)
    place_types: Optional[str] = None
    language: str = "vi"
    session_token: str = Field(..., min_length=1)


class PhotoInfo(BaseModel):
    photo_url: str
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


class NearbyPlaceRequest(BaseModel):
    location: Location
    radius: Optional[int]
    rank_by: str = "prominence"
    place_type: Optional[str] = None
    keyword: Optional[str] = None


class NearbyPlaceSimple(BaseModel):
    place_id: str
    name: str
    location: Location
    rating: Optional[float] = None
    types: List[str]


class NearbyPlacesResponse(BaseModel):
    center: Location
    places: List[NearbyPlaceSimple]
    next_page_token: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SearchAlongRouteResponse(BaseModel):
    places_along_route: List[NearbyPlaceSimple]

    model_config = ConfigDict(from_attributes=True)


class PlaceDataCategory(str, Enum):
    BASIC = "basic"
    CONTACT = "contact"
    ATMOSPHERE = "atmosphere"


class PlaceDetailsRequest(BaseModel):
    place_id: str = Field(..., min_length=1)
    session_token: Optional[str] = Field(None, min_length=1)
    categories: List[PlaceDataCategory] = Field(default=[PlaceDataCategory.BASIC])


class LocalizedText(BaseModel):
    text: str
    language_code: Optional[str] = Field(None, alias="languageCode")


class TextSearchRequest(BaseModel):
    query: str = Field(..., min_length=2)
    location: Optional[Location] = None
    radius: Optional[int] = Field(None, ge=100, le=50000)
    place_types: Optional[str] = None
    field_mask: Optional[List[str]] = None


class PlaceSearchResult(BaseModel):
    place_id: str = Field(alias="id")
    display_name: Optional[LocalizedText] = Field(None, alias="displayName")
    formatted_address: Optional[str] = Field(None, alias="formattedAddress")
    location: Optional[Location] = None
    types: List[str] = []
    photos: Optional[PhotoInfo] = None

    model_config = ConfigDict(populate_by_name=True)


class TextSearchResponse(BaseModel):
    results: List[PlaceSearchResult] = Field(default_factory=list, alias="places")

    model_config = ConfigDict(from_attributes=True)
