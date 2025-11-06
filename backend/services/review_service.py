from fastapi import HTTPException, status
from repository.review_repository import ReviewRepository
from repository.destination_repository import DestinationRepository
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.review_schema import ReviewCreate, ReviewUpdate

# Note: ReviewService now uses destination database
# Reviews are stored in the destination database alongside destination data

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
    async def create_review(
        dest_db: AsyncSession,
        review_data: ReviewCreate, 
        user_id: int
    ):
        """
        Create a review with destination validation.
        Uses destination_db since reviews are now in the destination database.
        """
        try:
            # Verify destination exists in destination database
            destination = await DestinationRepository.get_destination_by_id(
                dest_db, 
                review_data.destination_id
            )
            if not destination:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Destination with ID {review_data.destination_id} not found"
                )
            
            # Create review in destination database
            new_review = await ReviewRepository.create_review(dest_db, review_data, user_id)
            if not new_review:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create review"
                )
            return new_review
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
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error deleting review ID {review_id}: {e}"
            )