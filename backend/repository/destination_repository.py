from typing import List, Optional
from sqlalchemy import and_, delete, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from models.destination import *
from schemas.destination_schema import *


class DestinationRepository:
    @staticmethod
    async def get_destination_by_id(db: AsyncSession, destination_id: str):
        try:
            result = await db.execute(
                select(Destination).where(Destination.place_id == destination_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(
                f"ERROR: Failed to retrieve destination with ID {destination_id} - {e}"
            )
            return None

    @staticmethod
    async def create_destination(db: AsyncSession, destination: DestinationCreate):
        try:
            has_existing = await DestinationRepository.get_destination_by_id(
                db, destination.place_id
            )
            if has_existing:
                return has_existing
            new_destination = Destination(
                place_id=destination.place_id,
            )
            if destination.green_verified_status is not None:
                new_destination.green_verified = destination.green_verified_status
            db.add(new_destination)
            await db.commit()
            await db.refresh(new_destination)
            return new_destination
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Failed to create destination - {e}")
            return None

    @staticmethod
    async def update_destination(
        db: AsyncSession, destination_id: str, updated_data: DestinationUpdate
    ) -> Optional[Destination]:
        try:
            update_dict = {
                k: v
                for k, v in updated_data.model_dump(exclude_unset=True).items()
                if v is not None
            }

            if not update_dict:
                return await DestinationRepository.get_destination_by_id(
                    db, destination_id
                )

            if "green_verified_status" in update_dict:
                update_dict["green_verified"] = update_dict.pop("green_verified_status")

            stmt = (
                update(Destination)
                .where(Destination.place_id == destination_id)
                .values(**update_dict)
                .returning(Destination)
            )
            result = await db.execute(stmt)
            await db.commit()

            destination = result.scalar_one_or_none()
            if destination:
                await db.refresh(destination)
            return destination
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Failed to update destination with ID {destination_id} - {e}")
            return None

    @staticmethod
    async def delete_destination(db: AsyncSession, destination_id: str):
        try:
            stmt = delete(Destination).where(Destination.place_id == destination_id)
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Failed to delete destination with ID {destination_id} - {e}")
            return False

    @staticmethod
    async def save_destination_for_user(
        db: AsyncSession, user_id: int, destination_id: str
    ):
        try:
            existing = await DestinationRepository.is_saved_destination(
                db, user_id, destination_id
            )
            if existing:
                result = await db.execute(
                    select(UserSavedDestination).where(
                        and_(
                            UserSavedDestination.user_id == user_id,
                            UserSavedDestination.destination_id == destination_id,
                        )
                    )
                )
                return result.scalar_one_or_none()

            new_saved_destination = UserSavedDestination(
                user_id=user_id,
                destination_id=destination_id,
            )
            db.add(new_saved_destination)
            await db.commit()
            await db.refresh(new_saved_destination)
            return new_saved_destination
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Failed to save destination for user ID {user_id} - {e}")
            return None

    @staticmethod
    async def get_saved_destinations_for_user(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(
                select(UserSavedDestination).where(
                    UserSavedDestination.user_id == user_id
                )
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(
                f"ERROR: Failed to retrieve saved destinations for user ID "
                f"{user_id} - {e}"
            )
            return []

    @staticmethod
    async def delete_saved_destination(
        db: AsyncSession, user_id: int, destination_id: str
    ):
        try:
            stmt = delete(UserSavedDestination).where(
                and_(
                    UserSavedDestination.user_id == user_id,
                    UserSavedDestination.destination_id == destination_id,
                )
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Failed to delete saved destination - {e}")
            return False

    @staticmethod
    async def is_saved_destination(db: AsyncSession, user_id: int, destination_id: str):
        try:
            result = await db.execute(
                select(UserSavedDestination).where(
                    UserSavedDestination.user_id == user_id,
                    UserSavedDestination.destination_id == destination_id,
                )
            )
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            print(
                f"ERROR: Failed to check saved destination for user {user_id} "
                f"and destination {destination_id} - {e}"
            )
            return False

    @staticmethod
    async def get_popular_destinations(db: AsyncSession, limit: int = 10):
        try:
            query = (
                select(
                    UserSavedDestination.destination_id,
                    func.count(UserSavedDestination.user_id).label("save_count"),
                )
                .group_by(UserSavedDestination.destination_id)
                .order_by(func.count(UserSavedDestination.user_id).desc())
                .limit(limit)
            )
            result = await db.execute(query)
            return [
                {"destination_id": row[0], "save_count": row[1]} for row in result.all()
            ]
        except SQLAlchemyError as e:
            print(f"ERROR: Failed to get popular destinations - {e}")
            return []

    @staticmethod
    async def save_embedding(
        db: AsyncSession, embedding_data: DestinationEmbeddingCreate
    ):
        try:
            result = await db.execute(
                select(DestinationEmbedding).where(
                    DestinationEmbedding.destination_id == embedding_data.destination_id
                )
            )
            embedding = result.scalar_one_or_none()

            if embedding:
                embedding.set_vector(embedding_data.embedding_vector)
                embedding.model_version = embedding_data.model_version
                embedding.updated_at = func.now()
            else:
                embedding = DestinationEmbedding(
                    destination_id=embedding_data.destination_id,
                    model_version=embedding_data.model_version,
                )
                embedding.set_vector(embedding_data.embedding_vector)
                db.add(embedding)

            await db.commit()
            await db.refresh(embedding)
            return embedding
        except SQLAlchemyError as e:
            await db.rollback()
            print(
                f"ERROR: Failed to save embedding for "
                f"{embedding_data.destination_id} - {e}"
            )
            return None

    @staticmethod
    async def get_embedding(db: AsyncSession, destination_id: str):
        try:
            result = await db.execute(
                select(DestinationEmbedding).where(
                    DestinationEmbedding.destination_id == destination_id
                )
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"ERROR: Failed to get embedding for {destination_id} - {e}")
            return None

    @staticmethod
    async def get_embeddings_by_model(
        db: AsyncSession, model_version: str, skip: int = 0, limit: int = 1000
    ):
        try:
            query = (
                select(DestinationEmbedding)
                .where(DestinationEmbedding.model_version == model_version)
                .offset(skip)
                .limit(limit)
            )
            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: Failed to get embeddings for model {model_version} - {e}")
            return []

    @staticmethod
    async def delete_embedding(db: AsyncSession, destination_id: str):
        try:
            stmt = delete(DestinationEmbedding).where(
                DestinationEmbedding.destination_id == destination_id
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Failed to delete embedding for {destination_id} - {e}")
            return False

    @staticmethod
    async def get_all_destinations(db: AsyncSession, skip: int = 0, limit: int = 100):
        try:
            result = await db.execute(select(Destination).offset(skip).limit(limit))
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: Failed to retrieve all destinations - {e}")
            return []

    @staticmethod
    async def get_destinations_by_green_status(
        db: AsyncSession, status: GreenVerifiedStatus, skip: int = 0, limit: int = 100
    ):
        try:
            result = await db.execute(
                select(Destination)
                .where(Destination.green_verified == status)
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(
                f"ERROR: Failed to retrieve destinations by green status "
                f"{status} - {e}"
            )
            return []

    @staticmethod
    async def search_destinations(db: AsyncSession, place_ids: List[str]):
        try:
            result = await db.execute(
                select(Destination).where(Destination.place_id.in_(place_ids))
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: Failed to search destinations - {e}")
            return []
