from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ClusterCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    algorithm: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

    @field_validator("name", "algorithm")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v.strip()

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Description cannot be empty or whitespace")
        return v.strip() if v else None


class ClusterUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    algorithm: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

    @field_validator("name", "algorithm", "description")
    @classmethod
    def validate_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v.strip() if v else None


class ClusterResponse(BaseModel):
    id: int
    name: str
    algorithm: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserClusterAssociationCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    cluster_id: int = Field(..., gt=0)


class UserClusterAssociationResponse(BaseModel):
    user_id: int
    cluster_id: int
    assigned_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClusterDestinationCreate(BaseModel):
    cluster_id: int = Field(..., gt=0)
    destination_id: str = Field(..., min_length=1)
    popularity_score: Optional[float] = Field(None, ge=0)


class ClusterDestinationUpdate(BaseModel):
    popularity_score: Optional[float] = Field(None, ge=0)


class ClusterDestinationResponse(BaseModel):
    cluster_id: int
    destination_id: str
    popularity_score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class PreferenceUpdate(BaseModel):
    weather_pref: Optional[Dict[str, Any]] = None
    attraction_types: Optional[List[str]] = None
    budget_range: Optional[Dict[str, float]] = None
    kids_friendly: Optional[bool] = None
    visited_destinations: Optional[List[str]] = None
    embedding: Optional[List[float]] = None
    weight: Optional[float] = Field(None, ge=0, le=10)
    cluster_id: Optional[int] = None


class PreferenceResponse(BaseModel):
    id: int
    user_id: int
    weather_pref: Optional[Dict[str, Any]] = None
    attraction_types: Optional[List[str]] = None
    budget_range: Optional[Dict[str, float]] = None
    kids_friendly: Optional[bool] = None
    visited_destinations: Optional[List[str]] = None
    embedding: Optional[List[float]] = None
    weight: Optional[float] = Field(None, ge=0, le=10)
    cluster_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class ClusteringStats(BaseModel):
    embeddings_updated: int
    users_clustered: int
    associations_created: int
    clusters_updated: int


class ClusteringResultResponse(BaseModel):
    success: bool
    message: str
    stats: ClusteringStats
