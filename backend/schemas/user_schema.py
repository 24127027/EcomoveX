from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional    

class UserCredentialUpdate(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_username: Optional[str] = Field(None, min_length=1, max_length=100)
    new_email: Optional[EmailStr] = None
    new_password: Optional[str] = Field(None, min_length=6)

    @field_validator('old_password', 'new_password')
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Password cannot be empty or whitespace")
        return v

    @field_validator('new_username')
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Username cannot be empty or whitespace")
        return v.strip() if v else None

class UserProfileUpdate(BaseModel):
    eco_point: Optional[int] = Field(None, ge=0)
    rank: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    eco_point: int
    rank: str

    model_config = ConfigDict(from_attributes=True)
    
class UserActivityCreate(BaseModel):
    activity_type: str
    destination_id: int