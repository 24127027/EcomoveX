from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator
from typing import Optional
from datetime import datetime
from models.message import MessageType, MessageStatus

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