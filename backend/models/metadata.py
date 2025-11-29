from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.db import Base


class Metadata(Base):
    __tablename__ = "metadata"
    __table_args__ = (
        Index("ix_metadata_user_category", "user_id", "category"),
        Index("ix_metadata_uploaded", "uploaded_at"),
    )

    blob_name = Column(String(255), primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    filename = Column(String(255), nullable=False)
    content_type = Column(String(255), nullable=False)
    category = Column(String(255), nullable=False)
    bucket = Column(String(255), nullable=False)
    size = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="files")
    messages = relationship("Message", back_populates="file_metadata")
    rooms = relationship("Room", back_populates="file_metadata")
    review_files = relationship("ReviewFile", back_populates="file")
