import secrets
import random
import string
from fastapi import HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from repository.user_repository import UserRepository
from schemas.authentication_schema import (
    AuthenticationResponse,
    UserLogin,
    UserRegister,
)
from utils.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthenticationService:
    @staticmethod
    async def authenticate_user(db: AsyncSession, credentials: UserLogin):
        try:
            users = await UserRepository.search_users(db, credentials.email, limit=1)
            user = users[0] if users else None
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )
            if credentials.password != user.password:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )
            return user
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error authenticating user: {e}",
            )

    @staticmethod
    def create_access_token(user: User) -> str:
        try:
            payload = {
                "sub": str(user.id),
                "role": (
                    user.role.value if hasattr(user.role, "value") else str(user.role)
                ),
            }
            token = jwt.encode(
                payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
            )
            return token
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating access token: {e}",
            )

    @staticmethod
    async def login_user(
        db: AsyncSession, email: str, password: str
    ) -> AuthenticationResponse:
        try:
            users = await UserRepository.search_users(db, email, limit=1)
            user = users[0] if users else None
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )
            if password != user.password:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )
            token = AuthenticationService.create_access_token(user)
            return AuthenticationResponse(
                user_id=user.id, role=user.role, access_token=token, token_type="bearer"
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error logging in user: {e}",
            )

    @staticmethod
    async def register_user(
        db: AsyncSession, user_data: UserRegister
    ) -> AuthenticationResponse:
        try:
            new_user = await UserRepository.create_user(db, user_data)
            if not new_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create new user",
                )
            token = AuthenticationService.create_access_token(new_user)
            return AuthenticationResponse(
                user_id=new_user.id,
                role=new_user.role,
                access_token=token,
                token_type="bearer",
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error registering user: {e}",
            )

    @staticmethod
    async def generate_temporary_password(db: AsyncSession, email: str) -> str:
        try:
            is_user = await UserRepository.get_user_by_email(db, email)
            if not is_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User with the provided email does not exist",
                )
            # Random password length between 8-19 characters
            password_length = secrets.randbelow(12) + 8  # 8 to 19
            
            lowercase = string.ascii_lowercase
            uppercase = string.ascii_uppercase
            digits = string.digits
            symbols = string.punctuation

            # Ensure at least one character from each category
            password_chars = [
                secrets.choice(lowercase),
                secrets.choice(uppercase),
                secrets.choice(digits),
                secrets.choice(symbols),
            ]

            # Fill remaining characters randomly from all categories
            all_chars = lowercase + uppercase + digits + symbols
            password_chars += [secrets.choice(all_chars) for _ in range(password_length - 4)]

            # Securely shuffle the password characters
            secrets.SystemRandom().shuffle(password_chars)
            
            return ''.join(password_chars)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating temporary password: {e}",
            )