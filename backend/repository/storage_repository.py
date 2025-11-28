from models.metadata import *
from schemas.storage_schema import *
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

class StorageRepository:
    @staticmethod
    async def store_metadata(db: AsyncSession, metadata_data: MetadataCreate):
        try:
            new_metadata = Metadata(
                blob_name=metadata_data.blob_name,
                user_id=metadata_data.user_id,
                filename=metadata_data.filename,
                content_type=metadata_data.content_type,
                category=metadata_data.category,
                bucket=metadata_data.bucket,
                size=metadata_data.size
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
    
    @staticmethod
    async def update_metadata(
        db: AsyncSession,
        blob_name: str,
        updated_data: MetadataUpdate
    ):
        try:
            result = await db.execute(
                select(Metadata).where(Metadata.blob_name == blob_name)
            )
            metadata = result.scalar_one_or_none()
            
            if not metadata:
                print(f"WARNING: Metadata for blob {blob_name} not found")
                return None
            
            if updated_data.filename is not None:
                metadata.filename = updated_data.filename
            if updated_data.category is not None:
                metadata.category = updated_data.category
            
            db.add(metadata)
            await db.commit()
            await db.refresh(metadata)
            return metadata
        except Exception as e:
            await db.rollback()
            print(f"Error updating metadata for blob {blob_name}: {e}")
            return None
    
    @staticmethod
    async def get_file_count_by_user(db: AsyncSession, user_id: int, category: FileCategory = None):
        try:
            query = select(func.count(Metadata.blob_name)).where(Metadata.user_id == user_id)
            
            if category:
                query = query.where(Metadata.category == category.value)
            
            result = await db.execute(query)
            return result.scalar() or 0
        except Exception as e:
            print(f"Error counting files for user {user_id}: {e}")
            return 0
    
    @staticmethod
    async def get_total_size_by_user(db: AsyncSession, user_id: int, category: FileCategory = None):
        try:
            query = select(func.sum(Metadata.size)).where(Metadata.user_id == user_id)
            
            if category:
                query = query.where(Metadata.category == category.value)
            
            result = await db.execute(query)
            total_size = result.scalar()
            return total_size if total_size else 0
        except Exception as e:
            print(f"Error calculating total size for user {user_id}: {e}")
            return 0