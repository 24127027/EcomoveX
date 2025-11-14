from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional

class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    content: Optional[str] = None

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Review content cannot be empty or whitespace")
        return v.strip() if v else None

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    content: Optional[str] = None

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Review content cannot be empty or whitespace")
        return v.strip() if v else None

class ReviewResponse(BaseModel):
    destination_id: int
    user_id: int
    rating: int
    content: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)