from fastapi import HTTPException, status
from repository.review_repository import ReviewRepository
from sqlalchemy.ext.asyncio import AsyncSession
from schema.review_schema import ReviewCreate, ReviewUpdate

class ReviewService:
    @staticmethod
    async def get_reviews_by_destination(db: AsyncSession, destination_id: int):
        try:
            reviews = await ReviewRepository.get_reviews_by_destination(db, destination_id)
            return reviews
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving reviews for destination ID {destination_id}: {e}"
            )
        
    @staticmethod
    async def get_reviews_by_user(db: AsyncSession, user_id: int):
        try:
            reviews = await ReviewRepository.get_reviews_by_user(db, user_id)
            return reviews
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving reviews for user ID {user_id}: {e}"
            )
    
    @staticmethod
    async def create_review(db: AsyncSession, review_data: ReviewCreate):
        try:
            new_review = await ReviewRepository.create_review(db, review_data)
            if not new_review:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create review"
                )
            return new_review
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error creating review: {e}"
            )
        
    @staticmethod
    async def update_review(db: AsyncSession, review_id: int, updated_data: ReviewUpdate):
        try:
            updated_review = await ReviewRepository.update_review(db, review_id, updated_data)
            if not updated_review:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Review with ID {review_id} not found"
                )
            return updated_review
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error updating review ID {review_id}: {e}"
            )
        
    @staticmethod
    async def delete_review(db: AsyncSession, review_id: int):
        try:
            success = await ReviewRepository.delete_review(db, review_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Review with ID {review_id} not found"
                )
            return {"detail": "Review deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error deleting review ID {review_id}: {e}"
            )