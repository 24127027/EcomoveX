from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum
from models.chat import MessageStatus, MessageType

class MessageCreate(BaseModel):
    sender_id: int
    receiver_id: int
    content: Optional[str] = None
    message_type: MessageType = MessageType.text

class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: Optional[str]
    message_type: MessageType
    status: MessageStatus
    timestamp: datetime

    class Config:
        orm_mode = True

class ChatHistoryResponse(BaseModel):
    chat_id: int
    participants: List[int]
    messages: List[MessageResponse]

    class Config:
        orm_mode = True

class MessageUpdateStatus(BaseModel):
    message_id: int
    status: MessageStatus