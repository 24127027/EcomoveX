from sqlalchemy import Column, Integer, Float, String
from sqlalchemy.orm import relationship
from database.destination_database import DestinationBase
from enum import Enum

class Destination(DestinationBase):
    __tablename__ = "destinations"

    id = Column(Integer, primary_key=True, index=True)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    
    reviews = relationship("Review", back_populates="destination", cascade="all, delete-orphan")