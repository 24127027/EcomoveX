from pydantic import BaseModel
from typing import Optional, List

class BadgeCreate(BaseModel):
    name: str
    description: Optional[str] = None

class BadgeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class BadgeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        orm_mode = True

class UserBadgeResponse(BaseModel):
    user_id: int
    badge_id: int
    obtained_at: str

    class Config:
        orm_mode = True