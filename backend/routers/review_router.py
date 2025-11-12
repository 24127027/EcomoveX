from typing import List
from fastapi import APIRouter, Body, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import *
from database.destination_database import get_destination_db
from database.user_database import get_user_db
from schemas.review_schema import *
from schemas.user_schema import *
from services.review_service import ReviewService
from services.user_service import UserActivityService
from utils.token.authentication_util import get_current_user

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.get("/destination/{destination_id}", response_model=List[ReviewResponse], status_code=status.HTTP_200_OK)
async def get_reviews_by_destination(
    destination_id: int = Path(..., gt=0),
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
    destination_id: int = Path(..., gt=0),
    review_data: ReviewCreate = Body(...),
    dest_db: AsyncSession = Depends(get_destination_db),
    user_db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    result = await ReviewService.create_review(dest_db, current_user["user_id"], destination_id, review_data)
    try:
        activity_data = UserActivityCreate(
            activity=Activity.review_destination,
            destination_id=destination_id
        )
        await UserActivityService.log_user_activity(user_db, current_user["user_id"], activity_data)
    except Exception as e:
        # Log activity failure shouldn't break the main flow
        print(f"Warning: Failed to log activity - {e}")    
    return result

@router.put("/{destination_id}", response_model=ReviewResponse, status_code=status.HTTP_200_OK)
async def update_review(
    destination_id: int = Path(..., gt=0),
    updated_data: ReviewUpdate = ...,
    dest_db: AsyncSession = Depends(get_destination_db),
    current_user: dict = Depends(get_current_user)
):
    return await ReviewService.update_review(dest_db, current_user["user_id"], destination_id, updated_data)

@router.delete("/{destination_id}", status_code=status.HTTP_200_OK)
async def delete_review(
    destination_id: int = Path(..., gt=0),
    dest_db: AsyncSession = Depends(get_destination_db),
    current_user: dict = Depends(get_current_user)
):
    return await ReviewService.delete_review(dest_db, current_user["user_id"], destination_id)