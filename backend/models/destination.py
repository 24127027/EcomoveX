from enum import Enum
from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, PrimaryKeyConstraint, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.destination_database import DestinationBase
from database.user_database import UserBase

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

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    destination_id = Column(String(255), nullable=False, primary_key=True)
    saved_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="saved_destinations")