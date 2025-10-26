from pydantic import BaseModel, EmailStr
from typing import Optional
from models.user import UserStatus

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
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
    status: UserStatus
    eco_points: int
    rank: str

    class Config:
        orm_mode = True