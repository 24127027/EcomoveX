from enum import Enum
from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.db import UserBase

class MessageType(str, Enum):
    text = "text"
    file = "file"

class Sender(str, Enum):
    user = "user"
    bot = "bot"

class MessageStatus(str, Enum):
    sent = "sent"
    failed = "failed"

class Message(UserBase):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    sender = Column(SQLEnum(Sender), default=Sender.user)
    message_type = Column(SQLEnum(MessageType), default=MessageType.text)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.sent)

    user = relationship("User", back_populates="sent_messages")