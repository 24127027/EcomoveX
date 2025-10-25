from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.database import Base
import enum


class MessageType(str, enum.Enum):
    text = "text"
    image = "image"
    file = "file"


class MessageStatus(str, enum.Enum):
    sent = "sent"
    delivered = "delivered"
    read = "read"
    failed = "failed"


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Message content
    content = Column(Text)
    message_type = Column(
        SQLEnum(MessageType),
        default=MessageType.text,
        nullable=False
    )
    
    status = Column(
        SQLEnum(MessageStatus),
        default=MessageStatus.sent,
        nullable=False,
        index=True
    )
    
    file_url = Column(String(255))
    file_name = Column(String(255))
    file_size = Column(Integer)  # in bytes
    
    # Flags
    is_deleted_by_sender = Column(Boolean, default=False)
    is_deleted_by_receiver = Column(Boolean, default=False)
    is_edited = Column(Boolean, default=False)
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    delivered_at = Column(DateTime(timezone=True))
    read_at = Column(DateTime(timezone=True))
    edited_at = Column(DateTime(timezone=True))
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, sender_id={self.sender_id}, receiver_id={self.receiver_id})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "content": self.content,
            "message_type": self.message_type.value if self.message_type else None,
            "status": self.status.value if self.status else None,
            "file_url": self.file_url,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "is_deleted_by_sender": self.is_deleted_by_sender,
            "is_deleted_by_receiver": self.is_deleted_by_receiver,
            "is_edited": self.is_edited,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "edited_at": self.edited_at.isoformat() if self.edited_at else None
        }


class ChatRoom(Base):
    """Chat Room database model for group chats"""
    __tablename__ = "chat_rooms"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Room information
    name = Column(String(100))
    description = Column(Text)
    room_type = Column(String(50), default="private")  # private, group, channel
    
    # Room settings
    is_active = Column(Boolean, default=True)
    max_participants = Column(Integer, default=100)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ChatRoom(id={self.id}, name='{self.name}', type='{self.room_type}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "room_type": self.room_type,
            "is_active": self.is_active,
            "max_participants": self.max_participants,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class ChatParticipant(Base):
    """Chat Participant database model for tracking room members"""
    __tablename__ = "chat_participants"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    room_id = Column(Integer, ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Participant role
    role = Column(String(50), default="member")  # admin, moderator, member
    
    # Participant settings
    is_muted = Column(Boolean, default=False)
    notifications_enabled = Column(Boolean, default=True)
    
    # Timestamps
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<ChatParticipant(room_id={self.room_id}, user_id={self.user_id}, role='{self.role}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "room_id": self.room_id,
            "user_id": self.user_id,
            "role": self.role,
            "is_muted": self.is_muted,
            "notifications_enabled": self.notifications_enabled,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None
        }
