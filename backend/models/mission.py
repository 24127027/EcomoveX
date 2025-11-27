from enum import Enum
from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, Index, Integer, PrimaryKeyConstraint, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.db import Base

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
    __table_args__ = (
        Index('ix_mission_action_trigger', 'action_trigger'),
        Index('ix_mission_is_active', 'is_active'),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    reward_type = Column(SQLEnum(RewardType), nullable=False)
    action_trigger = Column(SQLEnum(MissionAction), nullable=False)
    value = Column(Integer, nullable=True, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("UserMission", back_populates="mission", cascade="all, delete-orphan")
    
class UserMission(Base):
    __tablename__ = "mission_users"
    __table_args__ = (
        Index('ix_user_mission_status', 'user_id', 'is_completed'),
    )
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    mission_id = Column(Integer, ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="missions")
    mission = relationship("Mission", back_populates="users")