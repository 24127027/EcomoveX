from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class FileCategory(str, Enum):
    profile_avatar = "profile_avatar"
    profile_cover = "profile_cover"
    review = "review"
    message = "message"

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

class MetadataCreate(BaseModel):
    blob_name: str = Field(..., min_length=1, max_length=255)
    user_id: int = Field(..., gt=0)
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=255)
    bucket: str = Field(..., min_length=1, max_length=255)
    size: int = Field(..., gt=0)

class MetadataUpdate(BaseModel):
    filename: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, min_length=1, max_length=255)

class MetadataResponse(BaseModel):
    blob_name: str
    user_id: int
    filename: str
    content_type: str
    category: str
    bucket: str
    size: int
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)