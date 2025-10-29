from sqlalchemy import Column, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from database.database import Base
from enum import Enum
from sqlalchemy.sql import func

class Role(str, Enum):
    user = "User"
    admin = "Admin"

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
    rank = Column(SQLEnum(Rank), default=Rank.bronze)
    role = Column(SQLEnum(Role), default=Role.user)
    created_at = Column(String, default=func.now())

    reviews = relationship("Review", back_populates="user")
    messages = relationship("Message", back_populates="user")
    badges = relationship("UserBadge", back_populates="user")
    media_files = relationship("MediaFile", back_populates="owner")
    plans = relationship("Plan", back_populates="user")