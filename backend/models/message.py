from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from database.database import Base
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

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    sender = Column(SQLEnum(Sender), default=Sender.user)
    message_type = Column(SQLEnum(MessageType), default=MessageType.text)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.sent)

    user = relationship("User", back_populates="sent_messages")