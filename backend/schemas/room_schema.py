from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime

class RoomCreate(BaseModel):
    room_name: str = Field(..., min_length=1, max_length=255)
    member_ids: List[int] = Field(default_factory=list)

class RoomResponse(BaseModel):
    id: int
    name: str
    user_id: int
    created_at: datetime
    member_ids: List[int] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)

class AddMemberRequest(BaseModel):
    ids: List[int] = Field(..., min_length=1)

class RemoveMemberRequest(BaseModel):
    ids: List[int] = Field(..., min_length=1)