from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum

class UserStatus(str, Enum):
    active = "active"
    offline = "offline"
    pending = "pending"
    suspended = "suspended"
    do_not_disturb = "do_not_disturb"

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    old_password: str
    new_username: Optional[str] = None
    new_email: Optional[EmailStr] = None
    new_password: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        orm_mode = True