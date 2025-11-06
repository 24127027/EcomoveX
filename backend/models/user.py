from sqlalchemy import Column, Integer, String, DateTime, PrimaryKeyConstraint, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from database.user_database import UserBase
from datetime import datetime, UTC
from enum import Enum
from sqlalchemy.sql import func

class Role(str, Enum):
    user = "User"
    admin = "Admin"

class Rank(str, Enum): # rank by eco point
    bronze = "Bronze" # 0 - 500
    silver = "Silver" # 501 - 2000
    gold = "Gold" # 2001 - 5000
    platinum = "Platinum" # 5001 - 10000
    diamond = "Diamond" # 10001+
    
def utc_now():
    return datetime.now(UTC).replace(tzinfo=None)

class User(UserBase):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    eco_point = Column(Integer, default=0)
    rank = Column(SQLEnum(Rank), default=Rank.bronze)
    role = Column(SQLEnum(Role), default=Role.user)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sent_messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    media_files = relationship("MediaFile", back_populates="owner", cascade="all, delete-orphan")
    plans = relationship("Plan", back_populates="user", cascade="all, delete-orphan")
    missions = relationship("UserMission", back_populates="user", cascade="all, delete-orphan")
    carbon_emissions = relationship("CarbonEmission", back_populates="user", cascade="all, delete-orphan")
    clusters = relationship("UserClusterAssociation", back_populates="user", cascade="all, delete-orphan")
    friends = relationship("Friend", foreign_keys="[Friend.user_id]", cascade="all, delete-orphan")
    saved_destinations = relationship("UserSavedDestination", back_populates="user", cascade="all, delete-orphan")