from typing import List, Optional

from fastapi import APIRouter, Depends, File, Path, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from models.user import Activity
from schemas.message_schema import CommonMessageResponse
from schemas.review_schema import (
    ReviewCreate,
    ReviewResponse,
    ReviewStatisticsResponse,
    ReviewUpdate,
)
from schemas.user_schema import (
    UserActivityCreate,
)
from services.review_service import ReviewService
from services.user_service import UserService
from utils.token.authentication_util import get_current_user

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("/me", response_model=List[ReviewResponse], status_code=status.HTTP_200_OK)
async def get_my_reviews(
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ReviewService.get_reviews_by_user(user_db, current_user["user_id"])


@router.get(
    "/destination/{destination_id}/statistics",
    response_model=ReviewStatisticsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_review_statistics(
    destination_id: str = Path(...), user_db: AsyncSession = Depends(get_db)
):
    return await ReviewService.get_review_statistics(user_db, destination_id)


@router.get(
    "/destination/{destination_id}",
    response_model=List[ReviewResponse],
    status_code=status.HTTP_200_OK,
)
async def get_reviews_by_destination(
    destination_id: str = Path(...), user_db: AsyncSession = Depends(get_db)
):
    return await ReviewService.get_reviews_by_destination(user_db, destination_id)


@router.post(
    "/{destination_id}",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    destination_id: str = Path(...),
    review_data: ReviewCreate = Depends(ReviewCreate.as_form),
    files: List[UploadFile] = File(default=[]),
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await ReviewService.create_review(
        user_db, current_user["user_id"], destination_id, review_data, files
    )
    activity_data = UserActivityCreate(
        activity=Activity.review_destination, destination_id=destination_id
    )
    await UserService.log_user_activity(user_db, current_user["user_id"], activity_data)
    return result


@router.put(
    "/{destination_id}", response_model=ReviewResponse, status_code=status.HTTP_200_OK
)
async def update_review(
    destination_id: str = Path(...),
    updated_data: ReviewUpdate = Depends(ReviewUpdate.as_form),
    files: Optional[List[UploadFile]] = File(default=None),
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ReviewService.update_review(
        user_db, current_user["user_id"], destination_id, updated_data, files
    )


@router.delete(
    "/{destination_id}",
    response_model=CommonMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_review(
    destination_id: str = Path(...),
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ReviewService.delete_review(
        user_db, current_user["user_id"], destination_id
    )
