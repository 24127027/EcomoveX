from sqlalchemy import Column, Integer, Float, String, PrimaryKeyConstraint, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database.destination_database import DestinationBase
from database.user_database import UserBase
from sqlalchemy.sql import func
from enum import Enum

class Destination(DestinationBase):
    __tablename__ = "destinations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    
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