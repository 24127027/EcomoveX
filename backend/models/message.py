from enum import Enum
from sqlalchemy import JSON, Column, DateTime, Enum as SQLEnum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.db import Base

class MessageType(str, Enum):
    text = "text"
    file = "file"

class MessageStatus(str, Enum):
    sent = "sent"
    seen = "seen"
    failed = "failed"

class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index('ix_message_room_created', 'room_id', 'created_at'),
        Index('ix_message_sender_created', 'sender_id', 'created_at'),
        Index('ix_message_room_status', 'room_id', 'status'),
        Index('ix_message_session', 'chat_session_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    chat_session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=True)
    message_type = Column(SQLEnum(MessageType), default=MessageType.text)
    file_blob_name = Column(String, ForeignKey("metadata.blob_name", ondelete="SET NULL"), nullable=True)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.sent)
    
    chat_session = relationship("ChatSession", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    room = relationship("Room", back_populates="messages")
    file_metadata = relationship("Metadata", back_populates="messages", foreign_keys=[file_blob_name])
    
class ChatSession(Base):
    __tablename__ = "chat_sessions"
    __table_args__ = (
        Index('ix_user_status', 'user_id', 'status'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(String(50), nullable=False, default="active", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)
    
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("Message", back_populates="chat_session", cascade="all, delete-orphan")
    contexts = relationship("ChatSessionContext", back_populates="session", cascade="all, delete-orphan")

class ChatSessionContext(Base):
    __tablename__ = "chat_session_context"
    __table_args__ = (
        Index('ix_session_key', 'session_id', 'key'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    key = Column(String(128), nullable=False)
    value = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    session = relationship("ChatSession", back_populates="contexts")