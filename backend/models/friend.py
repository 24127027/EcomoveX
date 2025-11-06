from sqlalchemy import Column, Integer, ForeignKey, DateTime, PrimaryKeyConstraint
from sqlalchemy.types import Enum as SQLEnum
from sqlalchemy.orm import relationship
from database.user_database import UserBase
from enum import Enum
from sqlalchemy.sql import func

class FriendStatus(str, Enum):
    pending = "Pending"
    accepted = "Accepted"
    blocked = "Blocked"
    
class Friend(UserBase):
    __tablename__ = "friends"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    friend_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    status = Column(SQLEnum(FriendStatus), default=FriendStatus.pending)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", foreign_keys=[user_id], back_populates="friends")
    friend = relationship("User", foreign_keys=[friend_id])