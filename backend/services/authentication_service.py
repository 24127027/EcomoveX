from datetime import datetime
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from .user_service import UserService
from schemas.authentication_schema import UserLogin, AuthenticationResponse, UserRegister
from models.user import User
from dotenv import load_dotenv
import os
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
env_path = backend_dir / "local.env"
load_dotenv(dotenv_path=env_path)

SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthenticationService:
    @staticmethod
    async def authenticate_user(db: AsyncSession, credentials: UserLogin):
        try:
            from repository.user_repository import UserRepository
            user = await UserRepository.get_user_by_email(db, credentials.email)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            if credentials.password != user.password:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            return user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error authenticating user: {e}"
            )

    @staticmethod
    def create_access_token(user: User) -> str:
        try:
            payload = {
                "sub": str(user.id),
                "role": user.role.value if hasattr(user.role, 'value') else str(user.role)
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
            return token
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating access token: {e}"
            )

    @staticmethod
    async def login_user(db: AsyncSession, email: str, password: str):
        try:
            from repository.user_repository import UserRepository
            user = await UserRepository.get_user_by_email(db, email)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            if password != user.password:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            token = AuthenticationService.create_access_token(user)
            return AuthenticationResponse(
                user_id=user.id,
                role=user.role,
                access_token=token,
                token_type="bearer"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error logging in user: {e}"
            )

    @staticmethod
    async def register_user(db: AsyncSession, user: UserRegister):
        try:
            from repository.user_repository import UserRepository
            
            # Check for duplicate email
            existing = await UserRepository.get_user_by_email(db, user.email)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Check for duplicate username
            existing_username = await UserRepository.get_user_by_username(db, user.username)
            if existing_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
            
            new_user = await UserRepository.create_user(db, user)
            if not new_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create new user"
                )
            token = AuthenticationService.create_access_token(new_user)
            return AuthenticationResponse(
                user_id=new_user.id,
                role=new_user.role,
                access_token=token,
                token_type="bearer"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error registering user: {e}"
            )