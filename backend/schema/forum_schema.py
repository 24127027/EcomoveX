from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class PostStatus(str, Enum):
    draft = "draft"
    published = "published"
    archived = "archived"

class ForumPostCreate(BaseModel):
    title: str
    content: str
    author_id: int
    status: Optional[PostStatus] = PostStatus.published

class ForumPostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[PostStatus] = None

class CommentCreate(BaseModel):
    post_id: int
    user_id: int
    content: str

class CommentResponse(BaseModel):
    id: int
    user_id: int
    content: str
    created_at: datetime

    class Config:
        orm_mode = True

class ForumPostResponse(BaseModel):
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