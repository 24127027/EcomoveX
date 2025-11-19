from enum import Enum
from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.db import Base

class MessageType(str, Enum):
    text = "text"
    file = "file"

class Sender(str, Enum):
    user = "user"
    bot = "bot" # bot have a unique user id (0)

class MessageStatus(str, Enum):
    sent = "sent"
    seen = "seen"
    failed = "failed"

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_type = Column(SQLEnum(MessageType), default=MessageType.text)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.sent)
    
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")