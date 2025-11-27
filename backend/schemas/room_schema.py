from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime
from models.room import MemberRole

class RoomCreate(BaseModel):
    room_name: str = Field(..., min_length=1, max_length=255)
    member_ids: List[int] = Field(default_factory=list)

class RoomResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    member_ids: List[int] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)
    
class DirectRoomResponse(BaseModel):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class AddMemberCreate(BaseModel):
    id: int
    role: MemberRole = MemberRole.member

class AddMemberRequest(BaseModel):
    data: List[AddMemberCreate] = Field(..., min_length=1)

class RemoveMemberRequest(BaseModel):
    ids: List[int] = Field(..., min_length=1)