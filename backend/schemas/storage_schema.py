from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class FileCategory(str, Enum):
    PROFILE_AVATAR = "profile_avatar"
    PROFILE_COVER = "profile_cover"
    TRAVEL_PHOTO = "travel_photo"

class FileSortBy(str, Enum):
    """Fields available for sorting file metadata."""
    FILENAME = "filename"
    SIZE = "size"
    UPLOADED_AT = "uploaded_at"
    UPDATED_AT = "updated_at"

class SortOrder(str, Enum):
    """Sort order direction."""
    ASC = "asc"
    DESC = "desc"

class FileMetadata(BaseModel):
    url: str = Field(...)
    blob_name: str = Field(...)
    filename: str = Field(...)
    content_type: str = Field(...)
    bucket: str = Field(...)
    size: int = Field(...)
    
class FileMetadataFilter(BaseModel):
    """Filter options for querying file metadata."""
    category: Optional[FileCategory] = Field(None, description="Filter by file category")
    content_type: Optional[str] = Field(None, description="Filter by MIME type (e.g., 'image/png')")
    uploaded_after: Optional[datetime] = Field(None, description="Files uploaded after this date")
    uploaded_before: Optional[datetime] = Field(None, description="Files uploaded before this date")
    sort_by: FileSortBy = Field(FileSortBy.UPLOADED_AT, description="Field to sort by")
    sort_order: SortOrder = Field(SortOrder.DESC, description="Sort direction")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")

    model_config = ConfigDict(use_enum_values=True)
class FileMetadataResponse(BaseModel):
    url: str = Field(...)
    blob_name: str = Field(...)
    filename: str = Field(...)
    content_type: str = Field(...)
    category: str = Field(...)
    size: int = Field(...)
    updated_at: Optional[datetime] = Field(None)

    model_config = ConfigDict(from_attributes=True)

