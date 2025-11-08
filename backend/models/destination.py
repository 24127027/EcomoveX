from sqlalchemy import Column, Integer, Float, String, PrimaryKeyConstraint, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database.destination_database import DestinationBase
from database.user_database import UserBase
from sqlalchemy.sql import func
from enum import Enum

class GreenVerifiedStatus(str, Enum):
    Green_Certified = "Green Certified"
    Not_Green_Verified = "Not Green Verified"
    AI_Green_Verified = "AI Green Verified"

class Destination(DestinationBase):
    __tablename__ = "destinations"

    google_place_id = Column(String(255), primary_key=True, nullable=False)
    green_verified = Column(SQLEnum(GreenVerifiedStatus), default=GreenVerifiedStatus.Not_Green_Verified)
    
    reviews = relationship("Review", back_populates="destination", cascade="all, delete-orphan")
    
class UserSavedDestination(UserBase):
    __tablename__ = "user_saved_destinations"
    
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'destination_id'),
    )

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    destination_id = Column(Integer, nullable=False)
    saved_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="saved_destinations")