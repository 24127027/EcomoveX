from datetime import datetime
from typing import List, Optional

from fastapi import Form
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    content: Optional[str] = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Review content cannot be empty or whitespace")
        return v.strip() if v else None

    @classmethod
    def as_form(
        cls, rating: int = Form(..., ge=1, le=5), content: Optional[str] = Form(None)
    ) -> "ReviewCreate":
        return cls(rating=rating, content=content)


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    content: Optional[str] = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Review content cannot be empty or whitespace")
        return v.strip() if v else None

    @classmethod
    def as_form(
        cls,
        rating: Optional[int] = Form(None, ge=1, le=5),
        content: Optional[str] = Form(None),
    ) -> "ReviewUpdate":
        return cls(rating=rating, content=content)


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
