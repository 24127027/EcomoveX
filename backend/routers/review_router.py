from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from database.destination_database import get_destination_db
from schemas.review_schema import ReviewCreate, ReviewUpdate, ReviewResponse
from services.review_service import ReviewService
from utils.authentication_util import get_current_user
from typing import List

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.get("/destination/{destination_id}", response_model=List[ReviewResponse], status_code=status.HTTP_200_OK)
async def get_reviews_by_destination(
    destination_id: int = Path(..., gt=0, description="Destination ID"),
    db: AsyncSession = Depends(get_destination_db)
):
    return await ReviewService.get_reviews_by_destination(db, destination_id)

@router.get("/me", response_model=List[ReviewResponse], status_code=status.HTTP_200_OK)
async def get_my_reviews(
    db: AsyncSession = Depends(get_destination_db),
    current_user: dict = Depends(get_current_user)
):
    return await ReviewService.get_reviews_by_user(db, current_user["user_id"])

@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    dest_db: AsyncSession = Depends(get_destination_db),
    current_user: dict = Depends(get_current_user)
):
    return await ReviewService.create_review(dest_db, review_data, current_user["user_id"])

@router.put("/{destination_id}", response_model=ReviewResponse, status_code=status.HTTP_200_OK)
async def update_review(
    destination_id: int = Path(..., gt=0, description="Destination ID"),
    updated_data: ReviewUpdate = ...,
    db: AsyncSession = Depends(get_destination_db),
    current_user: dict = Depends(get_current_user)
):
    return await ReviewService.update_review(db, destination_id, current_user["user_id"], updated_data)

@router.delete("/{destination_id}", status_code=status.HTTP_200_OK)
async def delete_review(
    destination_id: int = Path(..., gt=0, description="Destination ID"),
    db: AsyncSession = Depends(get_destination_db),
    current_user: dict = Depends(get_current_user)
):
    return await ReviewService.delete_review(db, destination_id, current_user["user_id"])