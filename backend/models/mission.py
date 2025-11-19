from enum import Enum
from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, PrimaryKeyConstraint, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.db import UserBase

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

class Mission(UserBase):
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    reward_type = Column(SQLEnum(RewardType), nullable=False)
    action_trigger = Column(SQLEnum(MissionAction), nullable=False)
    value = Column(Integer, nullable=True, default=0)

    users = relationship("UserMission", back_populates="mission")
    
class UserMission(UserBase):
    __tablename__ = "mission_users"
    
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'mission_id'),
    )

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    mission_id = Column(Integer, ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="missions")
    mission = relationship("Mission", back_populates="users")