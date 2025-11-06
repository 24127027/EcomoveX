from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from models.message import MessageType, MessageStatus, Sender

class MessageCreate(BaseModel):
    sender: Sender
    content: Optional[str] = Field(None, min_length=1)
    message_type: MessageType = MessageType.text

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Content cannot be empty or whitespace")
        return v

class MessageUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1)

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Content cannot be empty or whitespace")
        return v

class MessageResponse(BaseModel):
    id: int
    user_id: int
    sender: Sender
    content: Optional[str]
    message_type: MessageType
    status: MessageStatus
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)