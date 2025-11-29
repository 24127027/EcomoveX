from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from schemas.authentication_schema import *
from schemas.message_schema import CommonMessageResponse
from schemas.user_schema import *
from services.user_service import UserActivityService, UserService
from utils.token.authentication_util import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_my_profile(
    db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    return await UserService.get_user_by_id(db, current_user["user_id"])


@router.get("/id/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await UserService.get_user_by_id(db, user_id)


@router.get("/username/{username}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user_by_username(
    username: str,
    db: AsyncSession = Depends(get_db),
):
    return await UserService.get_user_by_username(db, username)


@router.get("/email/{email}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user_by_email(
    email: str,
    db: AsyncSession = Depends(get_db),
):
    return await UserService.get_user_by_email(db, email)


@router.put("/me/credentials", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user_credentials(
    updated_data: UserCredentialUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await UserService.update_user_credentials(db, current_user["user_id"], updated_data)


@router.put("/me/profile", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user_profile(
    updated_data: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await UserService.update_user_profile(db, current_user["user_id"], updated_data)


@router.delete("/me", response_model=CommonMessageResponse, status_code=status.HTTP_200_OK)
async def delete_user(
    db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    deleted = await UserService.delete_user(db, current_user["user_id"])
    if deleted:
        return {"message": "User deleted successfully"}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.post(
    "/{user_id}/eco_point/add",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def add_eco_point(
    user_id: int,
    point: int = Query(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can add eco point",
        )
    return await UserService.add_eco_point(db, user_id, point)


@router.post(
    "/{user_id}/activity",
    response_model=UserActivityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def log_user_activity(
    user_id: int,
    activity_data: UserActivityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can log activity for other users",
        )
    return await UserActivityService.log_user_activity(db, user_id, activity_data)
