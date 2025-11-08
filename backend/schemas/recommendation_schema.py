from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Tuple
from datetime import datetime
from enum import Enum

class RecommendationType(str, Enum):
    destination = "destination"
    transport = "transport"
    hotel = "hotel"
    restaurant = "restaurant"
    souvenir = "souvenir"

class RecommendationRequest(BaseModel):
    location: Tuple[float, float] = Field(..., description="Tọa độ (longitude, latitude)")
    search_radius_km: Optional[float] = Field(5.0, gt=0, le=100)
    preferred_type: Optional[RecommendationType] = RecommendationType.destination

class RecommendationItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    location: Tuple[float, float] = Field(..., description="Tọa độ (longitude, latitude)")
    category: RecommendationType
    eco_score: Optional[float] = Field(None, ge=0, le=100)
    price_range: Optional[str] = Field(None, max_length=50)
    image_url: Optional[str] = Field(None, max_length=500)
    link: Optional[str] = Field(None, max_length=500)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip()

class RecommendationResponse(BaseModel):
    user_id: int
    recommended_items: List[RecommendationItem]
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RecommendationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=1000)
    category: RecommendationType
    location: Tuple[float, float] = Field(..., description="Tọa độ (longitude, latitude)")
    eco_score: Optional[float] = Field(None, ge=0, le=100)
    price_range: Optional[str] = Field(None, max_length=50)
    image_url: Optional[str] = Field(None, max_length=500)
    link: Optional[str] = Field(None, max_length=500)

    @field_validator('name', 'description')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v.strip()