from fastapi import HTTPException, status
from repository.media_repository import MediaRepository
from sqlalchemy.ext.asyncio import AsyncSession
from schema.media_schema import MediaFileCreate, MediaFileUpdate

class MediaService:
    @staticmethod
    async def get_media_by_id(db: AsyncSession, media_id: int):
        try:
            media = await MediaRepository.get_media_by_id(db, media_id)
            if not media:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Media file with ID {media_id} not found"
                )
            return media
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving media file by ID {media_id}: {e}"
            )

    @staticmethod
    async def get_media_by_user(db: AsyncSession, user_id: int):
        try:
            media_files = await MediaRepository.get_media_by_user(db, user_id)
            return media_files
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving media files for user ID {user_id}: {e}"
            )
    
    @staticmethod
    async def create_media(db: AsyncSession, media_data: MediaFileCreate, user_id: int):
        try:
            new_media = await MediaRepository.create_media(db, media_data, user_id)
            if not new_media:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create media file"
                )
            return new_media
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error creating media file: {e}"
            )
    
    @staticmethod
    async def update_media(db: AsyncSession, media_id: int, updated_data: MediaFileUpdate):
        try:
            updated_media = await MediaRepository.update_media(db, media_id, updated_data)
            if not updated_media:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Media file with ID {media_id} not found"
                )
            return updated_media
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error updating media file ID {media_id}: {e}"
            )
    
    @staticmethod
    async def delete_media(db: AsyncSession, media_id: int):
        try:
            success = await MediaRepository.delete_media(db, media_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Media file with ID {media_id} not found"
                )
            return {"detail": "Media file deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error deleting media file ID {media_id}: {e}"
            )
