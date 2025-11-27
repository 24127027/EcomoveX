from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from models.message import MessageType, MessageStatus

class ChatMessage(BaseModel):
    user_id: int = Field(..., gt=0)
    session_id: int = Field(..., gt=0)
    message: str = Field(..., min_length=1)

class ChatbotResponse(BaseModel):
    response: str
    session_id: int
    metadata: Dict[str, Any] = {}

class CommonMessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None

class SuccessResponse(BaseModel):
    success: bool
    message: str

class SessionContextResponse(BaseModel):
    data: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)
    data: Optional[Dict[str, Any]] = None

class MessageCreate(BaseModel):
    content: Optional[str] = Field(None, min_length=1)
    message_type: MessageType = MessageType.text

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Content cannot be empty or whitespace")
        return v

class MessageResponse(BaseModel):
    id: int
    sender_id: int
    room_id: int
    content: Optional[str]
    message_type: MessageType
    status: MessageStatus
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
    
class WebSocketMessageRequest(BaseModel):
    content: Optional[str] = Field(None, min_length=1)
    message_type: MessageType = MessageType.text

    @model_validator(mode='after')
    def check_content_for_text(self):
        if self.message_type == MessageType.text:
            if not self.content or not self.content.strip():
                raise ValueError("Content cannot be empty for text message")
        return self

class WebSocketMessageResponse(BaseModel):
    type: str
    id: Optional[int] = None
    content: Optional[str] = None
    sender_id: Optional[int] = None
    room_id: Optional[int] = None
    timestamp: Optional[str] = None
    message_type: Optional[MessageType] = None
    status: Optional[MessageStatus] = None
    message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class ChatSessionCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    session_token: str = Field(..., min_length=1, max_length=255)
    status: str = Field("active", max_length=50)

class ChatSessionResponse(BaseModel):
    id: int
    user_id: int
    session_token: str
    status: str
    created_at: datetime
    last_active_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChatSessionContextCreate(BaseModel):
    session_id: int = Field(..., gt=0)
    key: str = Field(..., min_length=1, max_length=128)
    value: Optional[Dict[str, Any]] = None

class ChatSessionContextUpdate(BaseModel):
    value: Optional[Dict[str, Any]] = None

class ChatSessionContextResponse(BaseModel):
    id: int
    session_id: int
    key: str
    value: Optional[Dict[str, Any]] = None
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
    session_context: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class ContextUpdateRequest(BaseModel):
    user_message: str = Field(..., min_length=1)
    bot_message: str = Field(..., min_length=1)

class ContextSaveRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    session_id: int = Field(..., gt=0)
    history: List[MessageHistoryItem] = Field(default_factory=list)
    stored_context: Optional[StoredContextData] = None
    session_context: Optional[Dict[str, Any]] = None

class SessionContextRequest(BaseModel):
    session_id: int = Field(..., gt=0)
    key: str = Field(..., min_length=1, max_length=128)
    value: Optional[Dict[str, Any]] = None

class SessionContextResponse(BaseModel):
    session_id: int
    key: str
    value: Optional[Any] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)