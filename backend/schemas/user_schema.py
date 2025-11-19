from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from models.user import *

class UserCredentialUpdate(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_email: Optional[EmailStr] = None
    new_password: Optional[str] = Field(None, min_length=6)

    @field_validator('old_password', 'new_password')
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Password cannot be empty or whitespace")
        return v.strip() if v else None

class UserProfileUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=1, max_length=100)
    avt_blob_name: Optional[str] = None
    cover_blob_name: Optional[str] = None
        
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Username cannot be empty or whitespace")
        return v.strip() if v else None
    
class UserUpdateEcoPoint(BaseModel):
    point: int = Field(..., gt=0)
    rank: Optional[Rank] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    eco_point: int
    rank: str
    avt_url: Optional[str] = None
    cover_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class UserActivityCreate(BaseModel):
    activity: Activity
    destination_id: str
    
class UserActivityResponse(BaseModel):
    user_id: int
    destination_id: str
    activity: Activity
    timestamp: str

    model_config = ConfigDict(from_attributes=True)