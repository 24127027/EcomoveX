from pydantic import BaseModel, EmailStr
from models.user import Role

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class AuthenticationResponse(BaseModel):
    user_id: int
    role: Role  
    access_token: str
    token_type: str = "bearer"