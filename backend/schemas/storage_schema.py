from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class FileCategory(str, Enum):
    PROFILE_AVATAR = "profile_avatar"
    PROFILE_COVER = "profile_cover"
    TRAVEL_PHOTO = "travel_photo"

class FileSortBy(str, Enum):
    FILENAME = "filename"
    SIZE = "size"
    UPLOADED_AT = "uploaded_at"

class SortOrder(str, Enum):
    """Sort order direction."""
    ASCENDING = "ascending"
    DESCENDING = "descending"

class FileMetadata(BaseModel):
    url: str = Field(...)
    blob_name: str = Field(...)
    filename: str = Field(...)
    content_type: str = Field(...)
    bucket: str = Field(...)
    size: int = Field(...)
    
class FileMetadataFilter(BaseModel):
    category: Optional[FileCategory] = Field(None)
    content_type: Optional[str] = Field(None)
    uploaded_after: Optional[datetime] = Field(None)
    uploaded_before: Optional[datetime] = Field(None)
    sort_by: FileSortBy = Field(FileSortBy.UPLOADED_AT)
    sort_order: SortOrder = Field(SortOrder.DESCENDING)

class FileMetadataResponse(BaseModel):
    url: str = Field(...)
    blob_name: str = Field(...)
    filename: str = Field(...)
    content_type: str = Field(...)
    category: str = Field(...)
    size: int = Field(...)
    updated_at: Optional[datetime] = Field(None)

    model_config = ConfigDict(from_attributes=True)

