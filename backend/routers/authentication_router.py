from fastapi import APIRouter, Depends, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from schemas.authentication_schema import (
    AuthenticationResponse,
    UserLogin,
    UserRegister,
)
from services.authentication_service import AuthenticationService
from utils.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user_data: UserRegister, user_db: AsyncSession = Depends(get_db)
):
    result = await AuthenticationService.register_user(user_db, user_data)
    return {
        "message": "Verification email sent. Please check your email to complete registration.",
        "success": result
    }


@router.post(
    "/login", response_model=AuthenticationResponse, status_code=status.HTTP_200_OK
)
async def login_user(credentials: UserLogin, user_db: AsyncSession = Depends(get_db)):
    return await AuthenticationService.login_user(
        user_db, credentials.email, credentials.password
    )

  
@router.post(
    "/forgot-password", status_code=status.HTTP_200_OK
)
async def reset_password(
    email: str, 
    user_name: str,
    user_db: AsyncSession = Depends(get_db)
):
    return await AuthenticationService.reset_user_password(user_db, email, user_name)


@router.get(
    "/verify-email", status_code=status.HTTP_200_OK
)
async def verify_email_link(token: str, user_db: AsyncSession = Depends(get_db)):
    await AuthenticationService.verify_user_email(user_db, token)
    return RedirectResponse(
        url=settings.CORS_ORIGINS.split(',')[0],
        status_code=status.HTTP_302_FOUND
    )