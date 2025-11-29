from enum import Enum
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Enum as SQLEnum
from database.db import Base


class FriendStatus(str, Enum):
    pending = "pending"
    friend = "friend"


class Friend(Base):
    __tablename__ = "friends"
    __table_args__ = (
        PrimaryKeyConstraint("user1_id", "user2_id"),
        CheckConstraint("user1_id < user2_id", name="ck_user1_lt_user2"),
        Index("ix_friend_user1_status", "user1_id", "status"),
        Index("ix_friend_user2_status", "user2_id", "status"),
        Index("ix_friend_action_by", "action_by"),
    )

    user1_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user2_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status = Column(SQLEnum(FriendStatus), nullable=False, default=FriendStatus.pending)

    action_by = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user1 = relationship("User", foreign_keys=[user1_id], back_populates="friendships1")
    user2 = relationship("User", foreign_keys=[user2_id], back_populates="friendships2")
    action_user = relationship(
        "User", foreign_keys=[action_by], back_populates="friend_actions"
    )
