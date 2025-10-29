from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_db
from schema.authentication_schema import UserLogin, UserRegister, AuthenticationResponse
from services.authentication_service import AuthenticationService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=AuthenticationResponse)
async def register_user(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    return await AuthenticationService.register_user(db, user_data)

@router.post("/login", response_model=AuthenticationResponse)
async def login_user(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    return await AuthenticationService.login_user(db, credentials.email, credentials.password)