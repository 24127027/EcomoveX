from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from fastapi import UploadFile

class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    content: Optional[str] = None
    files: List[UploadFile] = Field(default_factory=list)

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Review content cannot be empty or whitespace")
        return v.strip() if v else None

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    content: Optional[str] = None
    files: Optional[List[UploadFile]] = None

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Review content cannot be empty or whitespace")
        return v.strip() if v else None

class ReviewResponse(BaseModel):
    destination_id: str
    user_id: int
    rating: int
    content: str
    created_at: datetime
    files_urls: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class ReviewStatisticsResponse(BaseModel):
    destination_id: str
    total_reviews: int
    average_rating: float
    rating_distribution: dict

    model_config = ConfigDict(from_attributes=True)