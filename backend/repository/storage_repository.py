import asyncio
from sqlalchemy.ext.asyncio import AsyncSession


class StorageRepository:
    @staticmethod
    async def store_metadata(db: AsyncSession, file_metadata: dict, user_id: int, category: str = None):
        pass

    @staticmethod
    async def get_metadata_by_blob_name(db: AsyncSession, blob_name: str):
        pass

    @staticmethod
    async def get_metadata_by_user_id(db: AsyncSession, user_id: int):
        pass

    @staticmethod
    async def delete_metadata_by_blob_name(db: AsyncSession, blob_name: str):
        pass

    @staticmethod
    async def update_metadata(db: AsyncSession, blob_name: str, updated_data: dict):
        pass

