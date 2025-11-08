from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, SmallInteger
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from database.destination_database import DestinationBase

class Review(DestinationBase):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    destination_id = Column(Integer, ForeignKey("destinations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, nullable=False)
    rating = Column(SmallInteger, nullable=False)
    content = Column(Text, nullable=False)
    
    destination = relationship("Destination", back_populates="reviews")