from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum

class FriendStatus(str, Enum):
    pending = "Pending"
    accepted = "Accepted"
    blocked = "Blocked"

class FriendRequest(BaseModel):
    friend_id: int = Field(..., gt=0)

class FriendResponse(BaseModel):
    user_id: int
    friend_id: int
    status: FriendStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)