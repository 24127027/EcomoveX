from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from schemas.message_schema import CommonMessageResponse
from schemas.user_schema import (
    UserCredentialUpdate,
    UserFilterParams,
    UserProfileUpdate,
    UserResponse,
)
from services.user_service import UserService
from utils.token.authentication_util import get_current_user
from utils.token.authorizer import require_roles

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_my_profile(
    db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    return await UserService.get_user_by_id(db, current_user["user_id"])


@router.get(
    "/id/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK
)
async def get_user_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await UserService.get_user_by_id(db, user_id)


@router.get(
    "/search/", response_model=List[UserResponse], status_code=status.HTTP_200_OK
)
async def search_users(
    query: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    return await UserService.search_users(db, query)


@router.put(
    "/me/credentials", response_model=UserResponse, status_code=status.HTTP_200_OK
)
async def update_user_credentials(
    updated_data: UserCredentialUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await UserService.update_user_credentials(
        db, current_user["user_id"], updated_data
    )


@router.put("/me/profile", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user_profile(
    updated_data: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await UserService.update_user_profile(
        db, current_user["user_id"], updated_data
    )


@router.delete(
    "/me", response_model=CommonMessageResponse, status_code=status.HTTP_200_OK
)
async def delete_user(
    db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    deleted = await UserService.delete_user(db, current_user["user_id"])
    if deleted:
        return {"message": "User deleted successfully"}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.delete(
    "/{user_id}",
    dependencies=[Depends(require_roles(["Admin"]))],
    status_code=status.HTTP_200_OK,
)
async def admin_delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    deleted = await UserService.delete_user(db, user_id)
    if deleted:
        return {"message": "User deleted successfully"}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.post(
    "/{user_id}/eco_point/add",
    dependencies=[Depends(require_roles(["Admin"]))],
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def add_eco_point(
    user_id: int,
    point: int = Query(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await UserService.add_eco_point(db, user_id, point)


@router.get(
    "/users",
    dependencies=[Depends(require_roles(["Admin"]))],
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
)
async def list_users(
    filters: UserFilterParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    return await UserService.list_users(db, filters)
