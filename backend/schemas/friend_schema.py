from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from models.friend import FriendStatus


class FriendResponse(BaseModel):
    user_id: int
    friend_id: int
    status: FriendStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FriendRequestByUsername(BaseModel):
    """Schema để gửi lời mời kết bạn bằng username"""

    username: str = Field(..., min_length=1, max_length=50, description="Username của người muốn kết bạn")

