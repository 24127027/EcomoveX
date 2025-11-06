from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from models.media import MediaFile
from datetime import datetime
from schemas.media_schema import MediaFileCreate, MediaFileUpdate

class MediaRepository:
    @staticmethod
    async def get_media_by_id(db: AsyncSession, media_id: int):
        try:
            result = await db.execute(select(MediaFile).where(MediaFile.id == media_id))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error retrieving media file by ID {media_id}: {e}")
            return None

    @staticmethod
    async def get_media_by_user(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(select(MediaFile).where(MediaFile.owner_id == user_id))
            return result.scalars().all()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error fetching media files for user ID {user_id}: {e}")
            return []

    @staticmethod
    async def create_media(db: AsyncSession, media_data: MediaFileCreate, user_id: int):
        try:
            new_media = MediaFile(
                owner_id=user_id,
                file_path=media_data.file_path,
                file_type=media_data.file_type.value
            )
            db.add(new_media)
            await db.commit()
            await db.refresh(new_media)
            return new_media
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error creating media file: {e}")
            return None

    @staticmethod
    async def update_media(db: AsyncSession, media_id: int, updated_data: MediaFileUpdate):
        try:
            result = await db.execute(select(MediaFile).where(MediaFile.id == media_id))
            media = result.scalar_one_or_none()
            if not media:
                print(f"Media file ID {media_id} not found")
                return None

            if updated_data.file_path is not None:
                media.file_path = updated_data.file_path
            if updated_data.file_type is not None:
                media.file_type = updated_data.file_type.value

            db.add(media)
            await db.commit()
            await db.refresh(media)
            return media
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error updating media file ID {media_id}: {e}")
            return None

    @staticmethod
    async def delete_media(db: AsyncSession, media_id: int):
        try:
            result = await db.execute(select(MediaFile).where(MediaFile.id == media_id))
            media = result.scalar_one_or_none()
            if not media:
                print(f"Media file ID {media_id} not found")
                return False

            await db.delete(media)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error deleting media file ID {media_id}: {e}")
            return False
