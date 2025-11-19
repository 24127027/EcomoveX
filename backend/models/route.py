from enum import Enum
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.user_database import UserBase

class TransportMode(str, Enum):
    car = "car"
    motorbike = "motorbike"
    walking = "walking"
    metro = "metro"
    bus = "bus"
    train = "train"
        
class RouteType(str, Enum):
    fastest = "fastest"
    low_carbon = "low_carbon"
    smart_combination = "smart_combination"

class Route(UserBase):
    __tablename__ = "routes"
    
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'origin_id', 'destination_id'),
    )

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    origin_id = Column(Integer, nullable=False, primary_key=True)
    destination_id = Column(Integer, nullable=False, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    distance_km = Column(Float, nullable=False)
    estimated_travel_time_min = Column(Float, nullable=False)
    carbon_emission_kg = Column(Float, nullable=False)
    
    user = relationship("User", back_populates="routes")