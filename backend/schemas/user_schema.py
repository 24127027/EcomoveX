from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from models.user import Activity, Rank


class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Username cannot be empty or whitespace")
        return v.strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Password cannot be empty or whitespace")
        return v.strip()


class UserCredentialUpdate(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_email: Optional[EmailStr] = None
    new_password: Optional[str] = Field(None, min_length=6)

    @field_validator("old_password", "new_password")
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Password cannot be empty or whitespace")
        return v.strip() if v else None


class UserProfileUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=1, max_length=100)
    avt_blob_name: Optional[str] = None
    cover_blob_name: Optional[str] = None

    @field_validator("username")
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
    role: str
    avt_url: Optional[str] = None
    cover_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserActivityCreate(BaseModel):
    activity: Activity
    destination_id: str


class UserActivityResponse(BaseModel):
    id: int
    user_id: int
    destination_id: str
    activity: Activity
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)



class UserFilterParams(BaseModel):
    role: Optional[str] = None
    status: Optional[str] = None
    search: Optional[str] = None
    created_from: Optional[date] = None
    created_to: Optional[date] = None
    skip: int = 0
    limit: int = 20
