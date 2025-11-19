from enum import Enum
from sqlalchemy import Column, DateTime, ForeignKey, Integer, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Enum as SQLEnum
from database.db import UserBase

class FriendStatus(str, Enum):
    requested = "Requested"
    pending = "Pending"
    friend = "Friend"
    
class Friend(UserBase):
    __tablename__ = "friends"
    
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'friend_id'),
    )

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    friend_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    status = Column(SQLEnum(FriendStatus), default=FriendStatus.pending)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", foreign_keys=[user_id], back_populates="friends")
    friend = relationship("User", foreign_keys=[friend_id])