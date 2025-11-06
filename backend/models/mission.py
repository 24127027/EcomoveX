from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from database.user_database import UserBase
from enum import Enum

class RewardType(str, Enum):
    eco_point = "eco_point"
    badge = "badge"

class MissionAction(str, Enum):
    register = "register"
    eco_trip = "eco_trip"
    forum_post = "forum_post"
    environment_protection = "environment_protection"
    daily_login = "daily_login"
    referral = "referral"

def utc_now():
    return datetime.now(UTC).replace(tzinfo=None)

class Mission(UserBase):
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    reward_type = Column(SQLEnum(RewardType), nullable=False)
    action_trigger = Column(SQLEnum(MissionAction), nullable=False)
    environment_protection_action = Column(Text, nullable=True)
    value = Column(Integer, nullable=True, default=0)

    users = relationship("UserMission", back_populates="mission")

class UserMission(UserBase):
    __tablename__ = "mission_users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mission_id = Column(Integer, ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)
    completed_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="missions")
    mission = relationship("Mission", back_populates="users")