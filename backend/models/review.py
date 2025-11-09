from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, SmallInteger, PrimaryKeyConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from database.destination_database import DestinationBase

class Review(DestinationBase):
    __tablename__ = "reviews"
    
    __table_args__ = (
        PrimaryKeyConstraint("destination_id", "user_id"),
    )

    destination_id = Column(Integer, ForeignKey("destinations.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    user_id = Column(Integer, nullable=False, primary_key=True)
    rating = Column(SmallInteger, nullable=False)
    content = Column(Text, nullable=False)
    
    destination = relationship("Destination", back_populates="reviews")