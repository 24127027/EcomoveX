from enum import Enum
from pydantic import BaseModel
from typing import Optional

class FileCategory(str, Enum):
    PROFILE_AVATAR = "profile_avatar"
    PROFILE_COVER = "profile_cover"
    TRAVEL_PHOTO = "travel_photo"
    
class FileUploadResponse(BaseModel):
    url: str
    blob_name: str
    content_type: str
    filename: str
    bucket: str
    size: int
    category: FileCategory

class FileDeleteResponse(BaseModel):
    detail: str