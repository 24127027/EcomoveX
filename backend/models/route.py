from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.user_database import UserBase

class Route(UserBase):
    __tablename__ = "routes"
    
    __table__args__ = (
        PrimaryKeyConstraint('user_id', 'origin_id', 'destination_id'),
    )

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    origin_id = Column(Integer, nullable=False)  # No FK - destination in separate DB
    destination_id = Column(Integer, nullable=False)  # No FK -
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    distance_km = Column(Float, nullable=False)
    estimated_travel_time_min = Column(Float, nullable=False)
    carbon_emission_kg = Column(Float, nullable=False)
    
    user = relationship("User", back_populates="routes")