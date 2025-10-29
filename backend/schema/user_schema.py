from pydantic import BaseModel, EmailStr
from typing import Optional    

class UserCredentialUpdate(BaseModel):
    old_password: str
    new_username: Optional[str] = None
    new_email: Optional[EmailStr] = None
    new_password: Optional[str] = None

class UserUpdate(BaseModel):
    eco_points: Optional[int] = None
    rank: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    eco_points: int
    rank: str

    class Config:
        orm_mode = True