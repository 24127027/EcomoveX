from sqlalchemy import CheckConstraint, Enum as SQLEnum, Column, DateTime, ForeignKey, Integer, PrimaryKeyConstraint, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.db import Base
from enum import Enum
class RoomType(str, Enum):
    direct = "direct"
    group = "group"
    
class MemberRole(str, Enum):
    admin = "admin"
    member = "member"

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    room_type = Column(SQLEnum(RoomType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    messages = relationship("Message", back_populates="room", cascade="all, delete-orphan")
    members = relationship("RoomMember", back_populates="room", cascade="all, delete-orphan")
    direct_info = relationship("RoomDirect", uselist=False, back_populates="room", cascade="all, delete-orphan")

    
class RoomDirect(Base):
    __tablename__ = "room_direct"
    __table_args__ = (
        UniqueConstraint("user1_id", "user2_id", name="uq_room_direct_pair"),
        CheckConstraint("user1_id < user2_id", name="ck_user1_lt_user2_direct"),
    )

    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), primary_key=True)
    user1_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user2_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    room = relationship("Room", back_populates="direct_info")
    user1 = relationship("User", foreign_keys=[user1_id])
    user2 = relationship("User", foreign_keys=[user2_id])
    
class RoomMember(Base):
    __tablename__ = "room_members"
    __table_args__ = (
        PrimaryKeyConstraint('room_id', 'user_id'),
    )

    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(SQLEnum(MemberRole), default=MemberRole.member, nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    room = relationship("Room", back_populates="members")
    user = relationship("User", back_populates="rooms")