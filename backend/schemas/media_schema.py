from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from models.media import FileType

class MediaFileCreate(BaseModel):
    file_path: str = Field(..., min_length=1)
    file_type: FileType

    @field_validator('file_path')
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("File path cannot be empty or whitespace")
        return v.strip()

class MediaFileUpdate(BaseModel):
    file_path: Optional[str] = Field(None, min_length=1)
    file_type: Optional[FileType] = None

    @field_validator('file_path')
    @classmethod
    def validate_file_path(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("File path cannot be empty or whitespace")
        return v.strip() if v else None

class MediaFileResponse(BaseModel):
    id: int
    owner_id: int
    file_path: str
    file_type: FileType
    uploaded_at: datetime

    model_config = {
        "from_attributes": True
    }