from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class FileCategory(str, Enum):
    PROFILE_AVATAR = "profile_avatar"
    PROFILE_COVER = "profile_cover"
    TRAVEL_PHOTO = "travel_photo"

class FileMetadata(BaseModel):
    url: str = Field(...)
    blob_name: str = Field(...)
    filename: str = Field(...)
    bucket: str = Field(...)
    size: int = Field(...)
    
class FileMetadataResponse(BaseModel):
    url: str = Field(...)
    content_type: str = Field(...)
    updated_at: Optional[datetime] = Field(None)