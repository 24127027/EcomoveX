from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from models.message import MessageStatus, MessageType


class ChatMessage(BaseModel):
    user_id: int = Field(..., gt=0)
    room_id: int = Field(..., gt=0)
    message: str = Field(..., min_length=1)


class ChatbotResponse(BaseModel):
    response: str
    room_id: int
    metadata: Dict[str, Any] = {}


class CommonMessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None


class SuccessResponse(BaseModel):
    success: bool
    message: str


class MessageResponse(BaseModel):
    id: int
    sender_id: int
    room_id: int
    plan_id: Optional[int] = None
    content: Optional[str]
    message_type: MessageType
    url: Optional[str] = None
    status: MessageStatus
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class RoomContextCreate(BaseModel):
    room_id: int = Field(..., gt=0)
    key: str = Field(..., min_length=1, max_length=128)
    value: Optional[Any] = None


class RoomContextUpdate(BaseModel):
    value: Optional[Any] = None


class RoomContextResponse(BaseModel):
    id: int
    room_id: int
    key: str
    value: Optional[Any] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageHistoryItem(BaseModel):
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = None


class StoredContextData(BaseModel):
    preferences: Optional[Dict[str, Any]] = None
    user_profile: Optional[Dict[str, Any]] = None
    past_trips: Optional[List[Dict[str, Any]]] = None
    custom_data: Optional[Dict[str, Any]] = None


class ActiveTripData(BaseModel):
    trip_id: Optional[int] = None
    destination: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[float] = None
    preferences: Optional[Dict[str, Any]] = None


class ActivityData(BaseModel):
    activity_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    scheduled_time: Optional[datetime] = None


class ContextLoadResponse(BaseModel):
    history: List[MessageHistoryItem] = Field(default_factory=list)
    stored_context: Optional[StoredContextData] = None
    active_trip: Optional[ActiveTripData] = None
    activities: List[ActivityData] = Field(default_factory=list)
    room_context: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class ContextUpdateRequest(BaseModel):
    user_message: str = Field(..., min_length=1)
    bot_message: str = Field(..., min_length=1)


class ContextSaveRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    room_id: int = Field(..., gt=0)
    history: List[MessageHistoryItem] = Field(default_factory=list)
    stored_context: Optional[StoredContextData] = None
    room_context: Optional[Dict[str, Any]] = None


class RoomContextRequest(BaseModel):
    room_id: int = Field(..., gt=0)
    key: str = Field(..., min_length=1, max_length=128)
    value: Optional[Dict[str, Any]] = None


class SessionContextResponse(BaseModel):
    room_id: int
    key: str
    value: Optional[Any] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
