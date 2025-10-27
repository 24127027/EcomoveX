from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from models.message import MessageType, MessageStatus, Sender

class MessageCreate(BaseModel):
    sender : Sender
    content: Optional[str] = None
    message_type: MessageType = MessageType.text

class MessageUpdate(BaseModel):
    content: Optional[str] = None

class MessageResponse(BaseModel):
    id: int
    user_id: int
    sender: Sender
    content: Optional[str]
    message_type: MessageType
    status: MessageStatus
    timestamp: datetime

    class Config:
        orm_mode = True

class MessageRoomResponse(BaseModel):
    room_id: int
    participants: List[int]
    messages: List[MessageResponse]

    class Config:
        orm_mode = True

class MessageUpdateStatus(BaseModel):
    message_id: int
    status: MessageStatus