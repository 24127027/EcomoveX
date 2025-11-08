from sqlalchemy import Column, Integer, String, DateTime, PrimaryKeyConstraint, Float, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from database.user_database import UserBase
from enum import Enum
from sqlalchemy.sql import func

class Role(str, Enum):
    user = "User"
    admin = "Admin"
    
class Activity(str, Enum):
    save_destination = "save destination"
    search_destination = "search destination"
    review_destination = "review destination"

class Rank(str, Enum):
    bronze = "Bronze"
    silver = "Silver"
    gold = "Gold"
    platinum = "Platinum"
    diamond = "Diamond"
    
class User(UserBase):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    temp_min = Column(Float, nullable=True, default=0)
    temp_max = Column(Float, nullable=True, default=0)
    budget_min = Column(Float, nullable=True, default=0)
    budget_max = Column(Float, nullable=True, default=0)
    eco_point = Column(Integer, nullable=True, default=0)
    rank = Column(SQLEnum(Rank), nullable=True, default=Rank.bronze)
    role = Column(SQLEnum(Role), nullable=True, default=Role.user)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sent_messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    plans = relationship("Plan", back_populates="user", cascade="all, delete-orphan")
    missions = relationship("UserMission", back_populates="user", cascade="all, delete-orphan")
    clusters = relationship("UserClusterAssociation", back_populates="user", cascade="all, delete-orphan")
    friends = relationship("Friend", foreign_keys="[Friend.user_id]", cascade="all, delete-orphan")
    saved_destinations = relationship("UserSavedDestination", back_populates="user", cascade="all, delete-orphan")
    routes = relationship("Route", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship("UserActivity", back_populates="user", cascade="all, delete-orphan")

class UserActivity(UserBase):
    __tablename__ = "user_activities"
    
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'destination_id'),
    )

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    destination_id = Column(Integer, primary_key=True)
    activity = Column(SQLEnum(Activity), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="activity_logs")