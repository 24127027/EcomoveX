from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from database.database import Base
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

class Mission(Base):
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    reward_type = Column(SQLEnum(RewardType), nullable=False)
    action_trigger = Column(SQLEnum(MissionAction), nullable=False)
    environment_protection_action = Column(Text, nullable=True)
    value = Column(Integer, nullable=True, default=0)

    users = relationship("UserMission", back_populates="mission")

class UserMission(Base):
    __tablename__ = "mission_users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mission_id = Column(Integer, ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)
    completed_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="missions")
    mission = relationship("Mission", back_populates="users")