from models.metadata import *
from schemas.storage_schema import *
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

class StorageRepository:
    @staticmethod
    async def store_metadata(db: AsyncSession, user_id: int, file_metadata: FileMetadata, category: FileCategory):
        try:
            new_metadata = Metadata(
                blob_name=file_metadata.blob_name,
                user_id=user_id,
                filename=file_metadata.filename,
                content_type=file_metadata.content_type,
                category=category.value,
                bucket=file_metadata.bucket,
                size=file_metadata.size
            )
            db.add(new_metadata)
            await db.commit()
            await db.refresh(new_metadata)
            return new_metadata
        except Exception as e:
            await db.rollback()
            raise

    @staticmethod
    async def get_metadata_by_blob_name(db: AsyncSession, blob_name: str):
        try:
            result = await db.execute(
                select(Metadata).where(
                    Metadata.blob_name == blob_name
                    )
                )
            return result.scalar_one_or_none()
        except Exception as e:
            print(f"Error retrieving metadata: {e}")
            return None

    @staticmethod
    async def get_user_files_metadata(
        db: AsyncSession, 
        user_id: int, 
        filters: FileMetadataFilter
    ) -> list[Metadata]:
        try:
            query = select(Metadata).where(Metadata.user_id == user_id)
            
            if filters:
                if filters.category:
                    query = query.where(Metadata.category == filters.category.value)
                
                if filters.content_type:
                    query = query.where(Metadata.content_type == filters.content_type)
                
                if filters.uploaded_after:
                    query = query.where(Metadata.uploaded_at >= filters.uploaded_after)
                if filters.uploaded_before:
                    query = query.where(Metadata.uploaded_at <= filters.uploaded_before)
                
                sort_column = getattr(Metadata, filters.sort_by.value, Metadata.uploaded_at)
                if filters.sort_order == SortOrder.ASCENDING:
                    query = query.order_by(sort_column.asc())
                else:
                    query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(Metadata.uploaded_at.desc())
            
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            print(f"Error retrieving metadata for user {user_id}: {e}")
            return []

    @staticmethod
    async def delete_metadata_by_blob_name(db: AsyncSession, blob_name: str):
        try:
            metadata = await db.execute(
                select(Metadata).where(Metadata.blob_name == blob_name)
            )
            metadata = metadata.scalar_one_or_none()
            
            if metadata:
                await db.delete(metadata)
                await db.commit()
                return True
            return False
        except Exception as e:
            await db.rollback()
            print(f"Error deleting metadata for blob {blob_name}: {e}")
            return False