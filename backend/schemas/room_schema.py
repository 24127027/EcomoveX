from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from models.room import MemberRole, RoomType


class RoomCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    room_type: RoomType = RoomType.group
    avatar_blob_name: Optional[str] = None
    member_ids: List[int] = Field(default_factory=list)


class RoomUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    avatar_blob_name: Optional[str] = None


class RoomResponse(BaseModel):
    id: int
    name: Optional[str] = None
    avatar_blob_name: Optional[str] = None
    room_type: RoomType
    created_at: datetime
    member_ids: List[int] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class RoomDirectResponse(BaseModel):
    room_id: int
    user1_id: int
    user2_id: int

    model_config = ConfigDict(from_attributes=True)

    role: MemberRole
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoomMemberCreate(BaseModel):
    user_id: int
    role: MemberRole = MemberRole.member


class AddMemberRequest(BaseModel):
    data: List[RoomMemberCreate] = Field(..., min_length=1)


class RemoveMemberRequest(BaseModel):
    ids: List[int] = Field(..., min_length=1)
