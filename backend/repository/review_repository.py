from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

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
    async def get_review_by_destination_and_user(
        db: AsyncSession, destination_id: str, user_id: int
    ):
        try:
            result = await db.execute(
                select(Review).where(
                    Review.destination_id == destination_id, Review.user_id == user_id
                )
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(
                f"ERROR: fetching review for destination {destination_id} and user {user_id} - {e}"
            )
            return None

    @staticmethod
    async def create_review(
        db: AsyncSession, user_id: int, destination_id: str, review_data: ReviewCreate
    ):
        try:
            new_review = Review(
                destination_id=destination_id,
                rating=review_data.rating,
                content=review_data.content or "",
                user_id=user_id,
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
    async def update_review(
        db: AsyncSession, user_id: int, destination_id: str, updated_data: ReviewUpdate
    ):
        try:
            review = await ReviewRepository.get_review_by_destination_and_user(
                db, destination_id, user_id
            )
            if not review:
                print(
                    f"WARNING: WARNING: Review for destination {destination_id} and user {user_id} not found"
                )
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
            print(
                f"ERROR: updating review for destination {destination_id} and user {user_id} - {e}"
            )
            return None

    @staticmethod
    async def delete_review(db: AsyncSession, user_id: int, destination_id: str):
        try:
            result = await db.execute(
                select(Review).where(
                    Review.destination_id == destination_id, Review.user_id == user_id
                )
            )
            review = result.scalar_one_or_none()
            if not review:
                print(
                    f"WARNING: WARNING: Review for destination {destination_id} and user {user_id} not found"
                )
                return False

            await db.delete(review)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(
                f"ERROR: deleting review for destination {destination_id} and user {user_id} - {e}"
            )
            return False

    @staticmethod
    async def get_review_statistics(db: AsyncSession, destination_id: str):
        try:
            result = await db.execute(
                select(
                    func.avg(Review.rating).label("avg_rating"),
                    func.count(Review.user_id).label("review_count"),
                ).where(Review.destination_id == destination_id)
            )
            stats = result.one()
            return {
                "avg_rating": float(stats.avg_rating) if stats.avg_rating else 0.0,
                "review_count": stats.review_count,
            }
        except SQLAlchemyError as e:
            print(f"ERROR: fetching review statistics for destination {destination_id} - {e}")
            return {"avg_rating": 0.0, "review_count": 0}

    @staticmethod
    async def add_review_file(db: AsyncSession, destination_id: str, user_id: int, blob_name: str):
        try:
            new_file = ReviewFile(
                destination_id=destination_id, user_id=user_id, blob_name=blob_name
            )
            db.add(new_file)
            await db.commit()
            await db.refresh(new_file)
            return new_file
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: adding file to review - {e}")
            return None

    @staticmethod
    async def get_review_files(db: AsyncSession, destination_id: str, user_id: int):
        try:
            result = await db.execute(
                select(ReviewFile).where(
                    ReviewFile.destination_id == destination_id,
                    ReviewFile.user_id == user_id,
                )
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching review files - {e}")
            return []

    @staticmethod
    async def get_review_files_by_user(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(
                select(ReviewFile).where(
                    ReviewFile.user_id == user_id,
                )
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching review files - {e}")
            return []

    @staticmethod
    async def remove_review_file(db: AsyncSession, blob_name: str):
        try:
            result = await db.execute(select(ReviewFile).where(ReviewFile.blob_name == blob_name))
            file = result.scalar_one_or_none()
            if not file:
                print(f"WARNING: Review file {blob_name} not found")
                return False

            await db.delete(file)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: removing review file {blob_name} - {e}")
            return False
