from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.user import Activity
from database.destination_database import get_destination_db
from database.user_database import get_user_db
from schemas.review_schema import ReviewCreate, ReviewUpdate, ReviewResponse
from schemas.user_schema import UserActivityCreate
from services.review_service import ReviewService
from services.user_service import UserActivityService
from utils.authentication_util import get_current_user
from typing import List

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.get("/destination/{destination_id}", response_model=List[ReviewResponse], status_code=status.HTTP_200_OK)
async def get_reviews_by_destination(
    destination_id: int = Path(..., gt=0, description="Destination ID"),
    dest_db: AsyncSession = Depends(get_destination_db)
):
    return await ReviewService.get_reviews_by_destination(dest_db, destination_id)

@router.get("/me", response_model=List[ReviewResponse], status_code=status.HTTP_200_OK)
async def get_my_reviews(
    dest_db: AsyncSession = Depends(get_destination_db),
    current_user: dict = Depends(get_current_user)
):
    return await ReviewService.get_reviews_by_user(dest_db, current_user["user_id"])

@router.post("/{destination_id}", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    destination_id: int = Path(..., gt=0, description="Destination ID"),
    review_data: ReviewCreate = ...,
    dest_db: AsyncSession = Depends(get_destination_db),
    user_db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    result = await ReviewService.create_review(dest_db, destination_id, review_data, current_user["user_id"])
    
    activity_data = UserActivityCreate(
        activity_type=Activity.review_destination,
        destination_id=destination_id
    )
    await UserActivityService.log_user_activity(user_db, current_user["user_id"], activity_data)
    
    return result

@router.put("/{destination_id}", response_model=ReviewResponse, status_code=status.HTTP_200_OK)
async def update_review(
    destination_id: int = Path(..., gt=0, description="Destination ID"),
    updated_data: ReviewUpdate = ...,
    dest_db: AsyncSession = Depends(get_destination_db),
    current_user: dict = Depends(get_current_user)
):
    return await ReviewService.update_review(dest_db, destination_id, current_user["user_id"], updated_data)

@router.delete("/{destination_id}", status_code=status.HTTP_200_OK)
async def delete_review(
    destination_id: int = Path(..., gt=0, description="Destination ID"),
    dest_db: AsyncSession = Depends(get_destination_db),
    current_user: dict = Depends(get_current_user)
):
    return await ReviewService.delete_review(dest_db, destination_id, current_user["user_id"])