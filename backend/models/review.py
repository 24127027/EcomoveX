from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from database.user_database import UserBase
import enum

class ReviewStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"

# Helper function to get current UTC time as naive datetime
def utc_now():
    return datetime.now(UTC).replace(tzinfo=None)

class Review(UserBase):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    destination_id = Column(Integer, nullable=False)  # No FK - destination in separate DB
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    status = Column(SQLEnum(ReviewStatus), default=ReviewStatus.draft)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="reviews")
