from pydantic import BaseModel, ConfigDict
from datetime import datetime
from models.friend import FriendStatus


class FriendResponse(BaseModel):
    user_id: int
    friend_id: int
    status: FriendStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
