from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from database.user_database import UserBase
from enum import Enum

class MessageType(str, Enum):
    text = "text"
    file = "file"

class Sender(str, Enum):
    user = "user"
    bot = "bot"

class MessageStatus(str, Enum):
    sent = "sent"
    failed = "failed"

# Helper function to get current UTC time as naive datetime
def utc_now():
    return datetime.now(UTC).replace(tzinfo=None)

class Message(UserBase):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    sender = Column(SQLEnum(Sender), default=Sender.user)
    message_type = Column(SQLEnum(MessageType), default=MessageType.text)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.sent)

    user = relationship("User", back_populates="sent_messages")