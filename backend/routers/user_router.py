from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_db
from schema.user_schema import UserCredentialUpdate, UserResponse
from schema.authentication_schema import UserRegister
from services.user_service import UserService
from utils.authentication_util import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await UserService.get_user_by_id(db, current_user["user_id"])

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: int, db: AsyncSession = Depends(get_db)):
    return await UserService.get_user_by_id(db, user_id)

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    return await UserService.create_user(db, user_data)

@router.put("/me/credentials", response_model=UserResponse)
async def update_user_credentials(
    updated_data: UserCredentialUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await UserService.update_user_credentials(db, current_user["user_id"], updated_data)

#only admin can do this
@router.post("/me/eco_points/add", response_model=UserResponse)
async def add_eco_points(
    points: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can add eco points"
        )
    return await UserService.add_eco_points(db, current_user["user_id"], points)