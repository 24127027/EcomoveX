from enum import Enum
from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, PrimaryKeyConstraint, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.db import Base

class GreenVerifiedStatus(str, Enum):
    Green_Certified = "Green Certified"
    Not_Green_Verified = "Not Green Verified"
    AI_Green_Verified = "AI Green Verified"

class Destination(Base):
    __tablename__ = "destinations"

    place_id = Column(String(255), primary_key=True, nullable=False)
    green_verified = Column(SQLEnum(GreenVerifiedStatus), default=GreenVerifiedStatus.Not_Green_Verified)

    reviews = relationship("Review", back_populates="destination", cascade="all, delete-orphan")
    plan_destinations = relationship("PlanDestination", back_populates="destination", cascade="all, delete-orphan")
    user_saved_destinations = relationship("UserSavedDestination", back_populates="destination", cascade="all, delete-orphan")
    cluster_destinations = relationship("ClusterDestination", back_populates="destination", cascade="all, delete-orphan")
    user_activities = relationship("UserActivity", back_populates="destination", cascade="all, delete-orphan")
    
class UserSavedDestination(Base):
    __tablename__ = "user_saved_destinations"
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'destination_id'),
    )

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    destination_id = Column(String(255), ForeignKey("destinations.place_id", ondelete="CASCADE"), nullable=False)
    saved_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="saved_destinations")
    destination = relationship("Destination", back_populates="user_saved_destinations")