from fastapi import HTTPException, status
from typing import List
from repository.review_repository import ReviewRepository
from repository.destination_repository import DestinationRepository
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.review_schema import ReviewCreate, ReviewUpdate, ReviewResponse

class ReviewService:
    @staticmethod
    async def get_reviews_by_destination(db: AsyncSession, destination_id: int)-> List[ReviewResponse]:
        try:
            reviews = await ReviewRepository.get_all_reviews_by_destination(db, destination_id)
            review_lists = []
            for review in reviews:
                review_lists.append(ReviewResponse(
                    destination_id=review.destination_id,
                    rating=review.rating,
                    content=review.content,
                    user_id=review.user_id
                ))
            return review_lists
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving reviews for destination ID {destination_id}: {e}"
            )
        
    @staticmethod
    async def get_reviews_by_user(db: AsyncSession, user_id: int) -> List[ReviewResponse]:
        try:
            reviews = await ReviewRepository.get_all_reviews_by_user(db, user_id)
            review_lists = []
            for review in reviews:
                review_lists.append(ReviewResponse(
                    destination_id=review.destination_id,
                    rating=review.rating,
                    content=review.content,
                    user_id=review.user_id
                ))
            return review_lists
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving reviews for user ID {user_id}: {e}"
            )
    
    @staticmethod
    async def create_review(dest_db: AsyncSession, user_id: int, destination_id: int, review_data: ReviewCreate) -> ReviewResponse:
        try:
            destination = await DestinationRepository.get_destination_by_id(dest_db, destination_id)
            if not destination:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Destination with ID {destination_id} not found"
                )
            
            new_review = await ReviewRepository.create_review(dest_db, user_id, destination_id, review_data)
            if not new_review:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create review"
                )
            return ReviewResponse(
                destination_id=new_review.destination_id,
                rating=new_review.rating,
                content=new_review.content,
                user_id=new_review.user_id
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error creating review: {e}"
            )
        
    @staticmethod
    async def update_review(db: AsyncSession, user_id: int, destination_id: int, updated_data: ReviewUpdate) -> ReviewResponse:
        try:
            updated_review = await ReviewRepository.update_review(db, user_id, destination_id, updated_data)
            if not updated_review:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Review for destination {destination_id} and user {user_id} not found"
                )
            return ReviewResponse(  
                destination_id=updated_review.destination_id,
                rating=updated_review.rating,
                content=updated_review.content,
                user_id=updated_review.user_id
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error updating review: {e}"
            )
        
    @staticmethod
    async def delete_review(db: AsyncSession, user_id: int, destination_id: int):
        try:
            success = await ReviewRepository.delete_review(db, user_id, destination_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Review for destination {destination_id} and user {user_id} not found"
                )
            return {"detail": "Review deleted successfully"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error deleting review: {e}"
            )