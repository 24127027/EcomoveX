from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from models.post import PostStatus
from .comment_schema import CommentResponse

class PostCreate(BaseModel):
    title: str
    content: str
    author_id: int
    status: Optional[PostStatus] = PostStatus.published

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[PostStatus] = None

class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    status: PostStatus
    created_at: datetime
    updated_at: datetime
    comments: Optional[List[CommentResponse]] = []

    class Config:
        orm_mode = True