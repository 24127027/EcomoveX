from typing import Any, Dict, List

from pydantic import BaseModel, Field


class RecommendationScore(BaseModel):
    destination_id: str
    hybrid_score: float
    similarity_score: float
    popularity_score: float


class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationScore] = Field(default_factory=list)


class SimpleRecommendation(BaseModel):
    """Simple recommendation with destination ID and similarity score from FAISS search"""
    destination_id: str
    similarity_score: float
    
    model_config = {"extra": "allow"}  # Allow extra fields for flexible responses

class RecommendationDestination(BaseModel):
    recommendation: List[str] = Field(default_factory=list)