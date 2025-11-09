from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.user_database import get_user_db
from schemas.authentication_schema import UserLogin, UserRegister, AuthenticationResponse
from services.authentication_service import AuthenticationService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=AuthenticationResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegister, db: AsyncSession = Depends(get_user_db)):
    return await AuthenticationService.register_user(db, user_data)

@router.post("/login", response_model=AuthenticationResponse, status_code=status.HTTP_200_OK)
async def login_user(credentials: UserLogin, db: AsyncSession = Depends(get_user_db)):
    return await AuthenticationService.login_user(db, credentials.email, credentials.password)