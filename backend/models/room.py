from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.db import Base


class RoomType(str, Enum):
    direct = "direct"
    group = "group"


class MemberRole(str, Enum):
    admin = "admin"
    member = "member"


class Room(Base):
    __tablename__ = "rooms"
    __table_args__ = (Index("ix_room_type_created", "room_type", "created_at"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    avatar_blob_name = Column(
        String(255),
        ForeignKey("metadata.blob_name", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    room_type = Column(SQLEnum(RoomType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    plan_id = Column(
        Integer, ForeignKey("plans.id", ondelete="SET NULL"), nullable=True, index=True
    )

    messages = relationship(
        "Message", back_populates="room", cascade="all, delete-orphan"
    )
    members = relationship(
        "RoomMember", back_populates="room", cascade="all, delete-orphan"
    )
    direct_info = relationship(
        "RoomDirect", uselist=False, back_populates="room", cascade="all, delete-orphan"
    )
    file_metadata = relationship(
        "Metadata", back_populates="rooms", foreign_keys=[avatar_blob_name]
    )
    contexts = relationship(
        "RoomContext", back_populates="room", cascade="all, delete-orphan"
    )
    plan = relationship("Plan", back_populates="room", uselist=False)


class RoomDirect(Base):
    __tablename__ = "room_direct"
    __table_args__ = (
        UniqueConstraint("user1_id", "user2_id", name="uq_room_direct_pair"),
        CheckConstraint("user1_id < user2_id", name="ck_user1_lt_user2_direct"),
        Index("ix_room_direct_users", "user1_id", "user2_id"),  # THÊM
    )

    room_id = Column(
        Integer, ForeignKey("rooms.id", ondelete="CASCADE"), primary_key=True
    )
    user1_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user2_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    room = relationship("Room", back_populates="direct_info")
    user1 = relationship("User", foreign_keys=[user1_id])
    user2 = relationship("User", foreign_keys=[user2_id])


class RoomMember(Base):
    __tablename__ = "room_members"
    __table_args__ = (
        PrimaryKeyConstraint("room_id", "user_id"),
        Index("ix_room_member_user", "user_id", "joined_at"),
        Index("ix_room_member_role", "room_id", "role"),
    )

    room_id = Column(
        Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role = Column(SQLEnum(MemberRole), default=MemberRole.member, nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    room = relationship("Room", back_populates="members")
    user = relationship("User", back_populates="rooms")
