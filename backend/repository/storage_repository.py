from models.metadata import *
from schemas.storage_schema import *
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class StorageRepository:
    @staticmethod
    async def store_metadata(db: AsyncSession, user_id: int, file_metadata: FileMetadata):
        try:
            new_metadata = Metadata(
                blob_name=file_metadata.blob_name,
                user_id=user_id,
                filename="image",
                url=file_metadata.url,
                content_type=file_metadata.content_type,
                bucket=file_metadata.bucket,
                size=file_metadata.size
            )
            db.add(new_metadata)
            await db.commit()
            await db.refresh(new_metadata)
            return new_metadata
        except Exception as e:
            await db.rollback()
            print(f"Error storing metadata: {e}")
            return None

    @staticmethod
    async def get_metadata_by_blob_name(db: AsyncSession, blob_name: str):
        try:
            result = await db.execute(
                select(Metadata).where(Metadata.blob_name == blob_name)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            print(f"Error retrieving metadata: {e}")
            return None

    @staticmethod
    async def get_metadata_by_user_id(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(
                select(Metadata).where(Metadata.user_id == user_id)
            )
            return result.scalars().all()
        except Exception as e:
            print(f"Error retrieving metadata for user {user_id}: {e}")
            return []

    @staticmethod
    async def delete_metadata_by_blob_name(db: AsyncSession, blob_name: str):
        try:
            metadata = await StorageRepository.get_metadata_by_blob_name(db, blob_name)
            if metadata:
                await db.delete(metadata)
                await db.commit()
                return True
            return False
        except Exception as e:
            await db.rollback()
            print(f"Error deleting metadata for blob {blob_name}: {e}")
            return False