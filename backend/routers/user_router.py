from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.user_database import get_user_db
from schemas.authentication_schema import *
from schemas.user_schema import *
from services.user_service import UserActivityService, UserService
from utils.authentication_util import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_my_profile(
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await UserService.get_user_by_id(db, current_user["user_id"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegister, db: AsyncSession = Depends(get_user_db)):
    return await UserService.create_user(db, user_data)

@router.put("/me/credentials", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user_credentials(
    updated_data: UserCredentialUpdate,
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await UserService.update_user_credentials(db, current_user["user_id"], updated_data)

@router.put("/me/profile", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user_profile(
    updated_data: UserProfileUpdate,
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await UserService.update_user_profile(db, current_user["user_id"], updated_data)

@router.delete("/me", status_code=status.HTTP_200_OK)
async def delete_user(
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    deleted = await UserService.delete_user(db, current_user["user_id"])
    if deleted:
        return {"message": "User deleted successfully"}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )

@router.post("/me/eco_point/add", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def add_eco_point(
    point: int = Query(..., gt=0, description="Eco points to add (must be positive)"),
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can add eco point"
        )
    return await UserService.add_eco_point(db, current_user["user_id"], point)

@router.get("/me/activity", response_model=List[UserActivityResponse], status_code=status.HTTP_200_OK)
async def get_user_activities(
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await UserActivityService.get_user_activities(db, current_user["user_id"])