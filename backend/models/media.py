from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from models.user import User
from database import Base
from enum import Enum

class FileType(str,Enum):
    image = "image"
    pdf = "pdf"
    video = "video"
    document = "document"
    audio = "audio"

class MediaFile(Base):
    __tablename__ = "media_file"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    file_path = Column(Text, nullable=False)
    file_type = Column(Enum(FileType), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="media_files")