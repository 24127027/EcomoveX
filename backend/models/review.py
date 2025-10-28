from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from database.database import Base
import enum

class ReviewStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    status = Column(SQLEnum(ReviewStatus), default=ReviewStatus.draft)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="reviews")
    destination = relationship("Destination")

