from pydantic import BaseModel, Field, field_validator, ConfigDict
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