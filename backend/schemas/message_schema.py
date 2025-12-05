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
    content: Optional[str]
    message_type: MessageType
    url: Optional[str] = None
    status: MessageStatus
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class RoomContextCreate(BaseModel):
    room_id: int = Field(..., gt=0)
    key: str = Field(..., min_length=1, max_length=128)
    value: Optional[Dict[str, Any]] = None


class MessageHistoryItem(BaseModel):
    role: str
    content: str
    timestamp: Optional[datetime] = None


class UserPreferences(BaseModel):
    preferred_activities: Optional[List[str]] = Field(default_factory=list)
    budget_range: Optional[str] = None
    travel_style: Optional[str] = None
    dietary_restrictions: Optional[List[str]] = Field(default_factory=list)
    language: Optional[str] = "vi"


class DestinationContext(BaseModel):
    destination_id: Optional[str] = None
    name: Optional[str] = None
    address: Optional[str] = None
    type: Optional[str] = None


class PlanDestinationContext(BaseModel):
    id: int
    destination_id: str
    name: Optional[str] = None
    visit_date: Optional[str] = None
    time_slot: Optional[str] = None
    order_in_day: Optional[int] = None
    note: Optional[str] = None


class ActivePlanContext(BaseModel):
    plan_id: int
    place_name: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    budget_limit: Optional[float] = None
    destinations: List[PlanDestinationContext] = Field(default_factory=list)


class ConversationState(BaseModel):
    current_intent: Optional[str] = None
    pending_action: Optional[str] = None
    last_mentioned_destination: Optional[DestinationContext] = None
    last_mentioned_date: Optional[str] = None
    last_mentioned_time_slot: Optional[str] = None
    awaiting_confirmation: bool = False
    missing_params: List[str] = Field(default_factory=list)


class LLMContextData(BaseModel):
    user_id: int
    user_preferences: Optional[UserPreferences] = None
    active_plan: Optional[ActivePlanContext] = None
    conversation_state: ConversationState = Field(default_factory=ConversationState)
    custom_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class StoredContextData(BaseModel):
    preferences: Optional[Dict[str, Any]] = None
    user_profile: Optional[Dict[str, Any]] = None
    past_trips: Optional[List[Dict[str, Any]]] = None
    custom_data: Optional[Dict[str, Any]] = None


class ActiveTripData(BaseModel):
    trip_id: Optional[int] = None
    place_name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget_limit: Optional[float] = None
    preferences: Optional[Dict[str, Any]] = None


class ContextLoadResponse(BaseModel):
    history: List[MessageHistoryItem] = Field(default_factory=list)
    llm_context: Optional[LLMContextData] = None
    stored_context: Optional[StoredContextData] = None
    active_trip: Optional[ActiveTripData] = None
    room_context: Dict[str, Any] = Field(default_factory=dict)

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


class RoomContextDataResponse(BaseModel):
    context: Dict[str, Any] = Field(default_factory=dict)
    room_id: int

    model_config = ConfigDict(from_attributes=True)
