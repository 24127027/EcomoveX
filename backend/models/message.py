from enum import Enum

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.db import Base


class MessageType(str, Enum):
    text = "text"
    file = "file"
    invitation = "invitation"



class MessageStatus(str, Enum):
    sent = "sent"
    seen = "seen"
    failed = "failed"


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_message_room_created", "room_id", "created_at"),
        Index("ix_message_sender_created", "sender_id", "created_at"),
        Index("ix_message_room_status", "room_id", "status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=True)
    message_type = Column(SQLEnum(MessageType), default=MessageType.text)
    file_blob_name = Column(
        String, ForeignKey("metadata.blob_name", ondelete="SET NULL"), nullable=True
    )
    content = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.sent)

    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    room = relationship("Room", back_populates="messages")
    file_metadata = relationship(
        "Metadata", back_populates="messages", foreign_keys=[file_blob_name]
    )


class RoomContext(Base):
    __tablename__ = "room_context"
    __table_args__ = (Index("ix_room_context_key", "room_id", "key"),)

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(
        Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key = Column(String(128), nullable=False)
    value = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    room = relationship("Room", back_populates="contexts")
