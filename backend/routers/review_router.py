from typing import List
from fastapi import APIRouter, Body, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import *
from database.database import get_db
from schemas.review_schema import *
from schemas.user_schema import *
from services.review_service import ReviewService
from services.user_service import UserActivityService
from utils.token.authentication_util import get_current_user

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.get("/destination/{destination_id}", response_model=List[ReviewResponse], status_code=status.HTTP_200_OK)
async def get_reviews_by_destination(
    destination_id: str = Path(...),
    user_db: AsyncSession = Depends(get_db)
):
    return await ReviewService.get_reviews_by_destination(user_db, destination_id)

@router.get("/me", response_model=List[ReviewResponse], status_code=status.HTTP_200_OK)
async def get_my_reviews(
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await ReviewService.get_reviews_by_user(user_db, current_user["user_id"])

@router.post("/{destination_id}", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    destination_id: str = Path(...),
    review_data: ReviewCreate = Body(...),
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    result = await ReviewService.create_review(user_db, current_user["user_id"], destination_id, review_data)
    try:
        activity_data = UserActivityCreate(
            activity=Activity.review_destination,
            destination_id=destination_id
        )
        await UserActivityService.log_user_activity(user_db, current_user["user_id"], activity_data)
    except Exception as e:
        print(f"Warning: Failed to log activity - {e}")    
    return result

@router.put("/{destination_id}", response_model=ReviewResponse, status_code=status.HTTP_200_OK)
async def update_review(
    destination_id: str = Path(...),
    updated_data: ReviewUpdate = ...,
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await ReviewService.update_review(user_db, current_user["user_id"], destination_id, updated_data)

@router.delete("/{destination_id}", status_code=status.HTTP_200_OK)
async def delete_review(
    destination_id: str = Path(...),
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await ReviewService.delete_review(user_db, current_user["user_id"], destination_id)