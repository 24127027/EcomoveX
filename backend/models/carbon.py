from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.database import Base
from enum import Enum

class VehicleType(str, Enum):
    car = "car"
    bus = "bus"
    motorbike = "motorbike"
    walk_or_cycle = "walk or cycle"

class FuelType(str, Enum):
    petrol = "petrol"
    diesel = "diesel"
    electric = "electric"
    hybrid = "hybrid"
    none = "none"

class CarbonEmission(Base):
    __tablename__ = "carbon_emissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    vehicle_type = Column(SQLEnum(VehicleType), nullable=False)
    distance_km = Column(Float, nullable=False)
    fuel_type = Column(SQLEnum(FuelType), nullable=False)
    carbon_emission_kg = Column(Float, nullable=False)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="carbon_emissions")
