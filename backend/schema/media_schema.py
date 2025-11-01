from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from models.media import FileType

class MediaFileCreate(BaseModel):
    file_path: str
    file_type: FileType

class MediaFileUpdate(BaseModel):
    file_path: Optional[str] = None
    file_type: Optional[FileType] = None

class MediaFileResponse(BaseModel):
    id: int
    owner_id: int
    file_path: str
    file_type: FileType
    uploaded_at: datetime

    model_config = {
        "from_attributes": True
    }