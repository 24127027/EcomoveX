from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from models.review import ReviewStatus

class ReviewCreate(BaseModel):
    destination_id: int = Field(..., gt=0)
    content: str = Field(..., min_length=1)
    status: Optional[ReviewStatus] = ReviewStatus.published

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Review content cannot be empty or whitespace")
        return v.strip()

class ReviewUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1)
    status: Optional[ReviewStatus] = None

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Review content cannot be empty or whitespace")
        return v.strip() if v else None

class ReviewResponse(BaseModel):
    id: int
    destination_id: int
    content: str
    user_id: int
    status: ReviewStatus
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }