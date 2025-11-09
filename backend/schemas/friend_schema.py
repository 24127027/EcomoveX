from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum
from models.friend import FriendStatus

class FriendRequest(BaseModel):
    friend_id: int = Field(..., gt=0)

class FriendResponse(BaseModel):
    user_id: int
    friend_id: int
    status: FriendStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)