from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime

class ReviewCreate(BaseModel):
    destination_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    content: Optional[str] = Field(None, description="Review content")

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Review content cannot be empty or whitespace")
        return v.strip() if v else None

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating from 1 to 5")
    content: Optional[str] = Field(None, description="Review content")

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Review content cannot be empty or whitespace")
        return v.strip() if v else None

class ReviewResponse(BaseModel):
    review_id: int = Field(alias="id")
    destination_id: int
    rating: int
    content: str
    user_id: int

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)