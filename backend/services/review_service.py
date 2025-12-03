from typing import List, Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from repository.destination_repository import DestinationRepository
from repository.review_repository import ReviewRepository
from schemas.review_schema import ReviewCreate, ReviewResponse, ReviewUpdate
from schemas.storage_schema import FileCategory
from services.storage_service import StorageService


class ReviewService:
    @staticmethod
    async def get_reviews_by_destination(
        db: AsyncSession, destination_id: str
    ) -> List[ReviewResponse]:
        try:
            reviews = await ReviewRepository.get_all_reviews_by_destination(
                db, destination_id
            )
            review_lists = []
            for review in reviews:
                urls = []
                files = await ReviewRepository.get_review_files(
                    db, destination_id, review.user_id
                )
                for file in files:
                    urls.append(
                        await StorageService.generate_signed_url(file.blob_name)
                    )
                review_lists.append(
                    ReviewResponse(
                        destination_id=review.destination_id,
                        rating=review.rating,
                        content=review.content,
                        user_id=review.user_id,
                        created_at=review.created_at,
                        files_urls=urls,
                    )
                )
            return review_lists
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"Unexpected error retrieving reviews for destination ID "
                    f"{destination_id}: {e}"
                ),
            )

    @staticmethod
    async def get_reviews_by_user(
        db: AsyncSession, user_id: int
    ) -> List[ReviewResponse]:
        try:
            reviews = await ReviewRepository.get_all_reviews_by_user(db, user_id)
            review_lists = []
            for review in reviews:
                urls = []
                files = await ReviewRepository.get_review_files(
                    db, review.destination_id, user_id
                )
                for file in files:
                    urls.append(
                        await StorageService.generate_signed_url(file.blob_name)
                    )
                review_lists.append(
                    ReviewResponse(
                        destination_id=review.destination_id,
                        rating=review.rating,
                        content=review.content,
                        user_id=review.user_id,
                        created_at=review.created_at,
                        files_urls=urls,
                    )
                )
            return review_lists
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving reviews for user ID {user_id}: {e}",
            )

    @staticmethod
    async def create_review(
        db: AsyncSession,
        user_id: int,
        destination_id: str,
        review_data: ReviewCreate,
        files: List[UploadFile] = None,
    ) -> ReviewResponse:
        try:
            destination = await DestinationRepository.get_destination_by_id(
                db, destination_id
            )
            if not destination:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Destination with ID {destination_id} not found",
                )

            new_review = await ReviewRepository.create_review(
                db, user_id, destination_id, review_data
            )
            if not new_review:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create review",
                )

            urls = []
            if files:
                for file in files:
                    metadata = await StorageService.upload_file(
                        db, file, user_id, FileCategory.review
                    )
                    urls.append(
                        await StorageService.generate_signed_url(metadata.blob_name)
                    )

            return ReviewResponse(
                destination_id=new_review.destination_id,
                rating=new_review.rating,
                content=new_review.content,
                user_id=new_review.user_id,
                created_at=new_review.created_at,
                files_urls=urls,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error creating review: {e}",
            )

    @staticmethod
    async def update_review(
        db: AsyncSession,
        user_id: int,
        destination_id: str,
        updated_data: ReviewUpdate,
        files: Optional[List[UploadFile]] = None,
    ) -> ReviewResponse:
        try:
            updated_review = await ReviewRepository.update_review(
                db, user_id, destination_id, updated_data
            )
            if not updated_review:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Review for destination {destination_id} and user {user_id} not found",
                )

            if files:
                for file in files:
                    await StorageService.upload_file(
                        db, file, user_id, FileCategory.review
                    )

            files = await ReviewRepository.get_review_files(db, destination_id, user_id)
            urls = []
            for file in files:
                urls.append(await StorageService.generate_signed_url(file.blob_name))

            return ReviewResponse(
                destination_id=updated_review.destination_id,
                rating=updated_review.rating,
                content=updated_review.content,
                user_id=updated_review.user_id,
                created_at=updated_review.created_at,
                files_urls=urls,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error updating review: {e}",
            )

    @staticmethod
    async def delete_review(db: AsyncSession, user_id: int, destination_id: str):
        try:
            success = await ReviewRepository.delete_review(db, user_id, destination_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Review for destination {destination_id} and user {user_id} not found",
                )
            return {"detail": "Review deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error deleting review: {e}",
            )

    @staticmethod
    async def get_review_statistics(db: AsyncSession, destination_id: str):
        try:
            stats = await ReviewRepository.get_review_statistics(db, destination_id)
            return stats
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving review statistics: {e}",
            )
