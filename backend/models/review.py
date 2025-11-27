from sqlalchemy import CheckConstraint, Column, DateTime, Enum as SQLEnum, ForeignKey, ForeignKeyConstraint, Index, Integer, PrimaryKeyConstraint, SmallInteger, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.db import Base

class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating_range"),
        Index('ix_review_destination_rating', 'destination_id', 'rating'),
        Index('ix_review_user', 'user_id', 'created_at'),
    )
    
    destination_id = Column(String(255), ForeignKey("destinations.place_id", ondelete="CASCADE"), nullable=False, primary_key=True)
    user_id = Column(Integer,ForeignKey("users.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    rating = Column(SmallInteger, nullable=False)
    content = Column(Text, nullable=False)
    files_blob_names = Column(Text, nullable=True)  # JSON array of blob names
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    destination = relationship("Destination", back_populates="reviews")
    user = relationship("User", back_populates="reviews")
    files = relationship("ReviewFile", back_populates="review", cascade="all, delete-orphan")

class ReviewFile(Base):
    __tablename__ = "review_files"
    __table_args__ = (
        Index('ix_review_file_destination_user', 'review_id'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    blob_name = Column(String(255), ForeignKey("metadata.blob_name", ondelete="CASCADE"), nullable=False, unique=True)

    file = relationship("Metadata", back_populates="review_files", foreign_keys=[blob_name])
    review = relationship("Review", back_populates="files", foreign_keys=[review_id])