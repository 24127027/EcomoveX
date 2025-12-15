from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from schemas.authentication_schema import (
    AuthenticationResponse,
    UserLogin,
    UserRegister,
)
from services.authentication_service import AuthenticationService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=AuthenticationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user_data: UserRegister, user_db: AsyncSession = Depends(get_db)
):
    return await AuthenticationService.register_user(user_db, user_data)


@router.post(
    "/login", response_model=AuthenticationResponse, status_code=status.HTTP_200_OK
)
async def login_user(credentials: UserLogin, user_db: AsyncSession = Depends(get_db)):
    return await AuthenticationService.login_user(
        user_db, credentials.email, credentials.password
    )
    
@router.post(
    "/forgot-password", response_model=str, status_code=status.HTTP_200_OK
)
async def reset_password(email: str, user_db: AsyncSession = Depends(get_db)):
    return await AuthenticationService.reset_user_password(user_db, email)