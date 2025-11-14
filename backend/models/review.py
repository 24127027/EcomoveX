from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, PrimaryKeyConstraint, SmallInteger, String, Text
from sqlalchemy.orm import relationship
from database.destination_database import DestinationBase

class Review(DestinationBase):
    __tablename__ = "reviews"
    
    __table_args__ = (
        PrimaryKeyConstraint("destination_id", "user_id"),
    )

    destination_id = Column(String(255), ForeignKey("destinations.google_place_id", ondelete="CASCADE"), nullable=False, primary_key=True)
    user_id = Column(Integer, nullable=False, primary_key=True)
    rating = Column(SmallInteger, nullable=False)
    content = Column(Text, nullable=False)
    
    destination = relationship("Destination", back_populates="reviews")