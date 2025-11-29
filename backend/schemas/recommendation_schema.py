from typing import List

from pydantic import BaseModel, Field


class RecommendationScore(BaseModel):
    destination_id: str
    hybrid_score: float
    similarity_score: float
    popularity_score: float


class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationScore] = Field(default_factory=list)
