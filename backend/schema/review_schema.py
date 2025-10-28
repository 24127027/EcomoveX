from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from models.review import ReviewStatus

class ReviewCreate(BaseModel):
    content: str
    user_id: int
    status: Optional[ReviewStatus] = ReviewStatus.published

class ReviewUpdate(BaseModel):
    content: Optional[str] = None
    status: Optional[ReviewStatus] = None

class ReviewResponse(BaseModel):
    id: int
    content: str
    user_id: int
    status: ReviewStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True