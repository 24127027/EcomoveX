from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class FileCategory(str, Enum):
    profile_avatar = "profile_avatar"
    profile_cover = "profile_cover"
    travel_photo = "travel_photo"
    message_photo = "message_photo"

class FileSortBy(str, Enum):
    FILENAME = "filename"
    SIZE = "size"
    UPLOADED_AT = "uploaded_at"

class SortOrder(str, Enum):
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