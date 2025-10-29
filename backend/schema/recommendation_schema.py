from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class RecommendationType(str, Enum):
    destination = "destination"
    transport = "transport"
    hotel = "hotel"
    restaurant = "restaurant"
    souvenir = "souvenir"

class RecommendationRequest(BaseModel):
    user_id: int
    longitude: float
    latitude: float
    search_radius_km: Optional[float] = 5.0
    preferred_type: Optional[RecommendationType] = RecommendationType.destination

class RecommendationItem(BaseModel):
    name: str
    description: Optional[str] = None
    longitude: float
    latitude: float
    category: RecommendationType
    eco_score: Optional[float] = None
    price_range: Optional[str] = None
    image_url: Optional[str] = None
    link: Optional[str] = None

class RecommendationResponse(BaseModel):
    user_id: int
    recommended_items: List[RecommendationItem]
    generated_at: datetime

    model_config = {
        "from_attributes": True
    }

class RecommendationCreate(BaseModel):
    name: str
    description: str
    category: RecommendationType
    longitude: float
    latitude: float
    eco_score: Optional[float] = None
    price_range: Optional[str] = None
    image_url: Optional[str] = None
    link: Optional[str] = None