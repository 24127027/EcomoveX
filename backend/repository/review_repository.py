from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from models.review import Review
from datetime import datetime, UTC
from schemas.review_schema import ReviewCreate, ReviewUpdate

# Note: This repository now uses the destination database (get_destination_db)
# Review model is part of DestinationBase and has proper FK to destinations table

class ReviewRepository:
    @staticmethod
    async def get_all_reviews(db: AsyncSession):
        try:
            result = await db.execute(select(Review))
            return result.scalars().all()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error fetching all reviews: {e}")
            return []

    @staticmethod
    async def get_review_by_id(db: AsyncSession, review_id: int):
        try:
            result = await db.execute(select(Review).where(Review.id == review_id))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error fetching review ID {review_id}: {e}")
            return None
        
    @staticmethod
    async def get_reviews_by_destination(db: AsyncSession, destination_id: int):
        try:
            result = await db.execute(select(Review).where(Review.destination_id == destination_id))
            return result.scalars().all()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error fetching reviews for destination ID {destination_id}: {e}")
            return []

    @staticmethod
    async def get_reviews_by_user(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(select(Review).where(Review.user_id == user_id))
            return result.scalars().all()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error fetching reviews by user {user_id}: {e}")
            return []

    @staticmethod
    async def create_review(db: AsyncSession, review_data: ReviewCreate, user_id: int):
        try:
            new_review = Review(
                destination_id=review_data.destination_id,
                rating=review_data.rating,
                content=review_data.content or "",
                user_id=user_id
            )
            db.add(new_review)
            await db.commit()
            await db.refresh(new_review)
            return new_review
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error creating review: {e}")
            return None

    @staticmethod
    async def update_review(db: AsyncSession, review_id: int, updated_data: ReviewUpdate):
        try:
            result = await db.execute(select(Review).where(Review.id == review_id))
            review = result.scalar_one_or_none()
            if not review:
                print(f"Review ID {review_id} not found")
                return None

            if updated_data.rating is not None:
                review.rating = updated_data.rating
            if updated_data.content is not None:
                review.content = updated_data.content

            db.add(review)
            await db.commit()
            await db.refresh(review)
            return review
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error updating review ID {review_id}: {e}")
            return None

    @staticmethod
    async def delete_review(db: AsyncSession, review_id: int):
        try:
            result = await db.execute(select(Review).where(Review.id == review_id))
            review = result.scalar_one_or_none()
            if not review:
                print(f"Review ID {review_id} not found")
                return False

            await db.delete(review)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error deleting review ID {review_id}: {e}")
            return False
