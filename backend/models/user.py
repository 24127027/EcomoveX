from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database.database import Base
from enum import Enum
from sqlalchemy import DateTime
from sqlalchemy.sql import func

class UserStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    pending = "pending"
    do_not_disturb = "do_not_disturb"

class Rank(str, Enum): # rank by eco points
    bronze = "Bronze" # 0 - 500
    silver = "Silver" # 501 - 2000
    gold = "Gold" # 2001 - 5000
    platinum = "Platinum" # 5001 - 10000
    diamond = "Diamond" # 10001+

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    eco_point = Column(Integer, default=0)
    rank = Column(Enum(Rank), default=Rank.bronze)
    status = Column(Enum(UserStatus), default=UserStatus.active)
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="author")
    sent_messages = relationship("Chat", foreign_keys="[Chat.sender_id]", back_populates="sender")
    received_messages = relationship("Chat", foreign_keys="[Chat.receiver_id]", back_populates="receiver")
    badges = relationship("UserBadge", back_populates="user")
    chat_rooms = relationship("ChatRoomMember", back_populates="user")
    media_files = relationship("MediaFile", back_populates="owner")