from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from models.review import *
from schemas.review_schema import *

class ReviewRepository:
    @staticmethod
    async def get_all_reviews_by_destination(db: AsyncSession, destination_id: str):
        try:
            result = await db.execute(select(Review).where(Review.destination_id == destination_id))
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching all reviews - {e}")
            return []

    @staticmethod
    async def get_all_reviews_by_user(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(select(Review).where(Review.user_id == user_id))
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching review for user {user_id} - {e}")
            return []
        
    @staticmethod
    async def get_review_by_destination_and_user(db: AsyncSession, destination_id: str, user_id: int):
        try:
            result = await db.execute(
                select(Review).where(
                    Review.destination_id == destination_id,
                    Review.user_id == user_id
                )
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching review for destination {destination_id} and user {user_id} - {e}")
            return None
        
    @staticmethod
    async def create_review(db: AsyncSession, user_id: int, destination_id: str, review_data: ReviewCreate):
        try:
            new_review = Review(
                destination_id=destination_id,
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
            print(f"ERROR: creating review - {e}")
            return None

    @staticmethod
    async def update_review(db: AsyncSession, user_id: int,destination_id: str, updated_data: ReviewUpdate):
        try:
            review = await ReviewRepository.get_review_by_destination_and_user(db, destination_id, user_id)
            if not review:
                print(f"WARNING: WARNING: Review for destination {destination_id} and user {user_id} not found")
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
            print(f"ERROR: updating review for destination {destination_id} and user {user_id} - {e}")
            return None

    @staticmethod
    async def delete_review(db: AsyncSession, user_id: int, destination_id: str):
        try:
            result = await db.execute(
                select(Review).where(
                    Review.destination_id == destination_id,
                    Review.user_id == user_id
                )
            )
            review = result.scalar_one_or_none()
            if not review:
                print(f"WARNING: WARNING: Review for destination {destination_id} and user {user_id} not found")
                return False

            await db.delete(review)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: deleting review for destination {destination_id} and user {user_id} - {e}")
            return False
