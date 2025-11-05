from pydantic import BaseModel, EmailStr, Field, field_validator
from models.user import Role

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)

class UserRegister(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Username cannot be empty or whitespace")
        return v.strip()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Password cannot be empty or whitespace")
        return v

class AuthenticationResponse(BaseModel):
    user_id: int
    role: Role  
    access_token: str
    token_type: str = "bearer"