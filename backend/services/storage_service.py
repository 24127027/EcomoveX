from fastapi import UploadFile, HTTPException, status
from google.cloud import storage
from sqlalchemy.ext.asyncio import AsyncSession
from backend.utils.config import settings
from backend.repository.storage_repository import StorageRepository
from backend.schemas.storage_schema import FileCategory, FileMetadataResponse
from backend.models.metadata import FileMetadata
import uuid
from datetime import timedelta
import asyncio


class StorageService:
    @staticmethod
    async def upload_file(db: AsyncSession,
                          file: UploadFile,
                          user_id: int,
                          category: FileCategory,
                          bucket_name: str = None
                          ) -> dict:
        """Upload a file to GCS and store metadata in database"""
        file_metadata = await StorageService.upload_file_to_gcs(file, category, bucket_name)
        
        # Store metadata in database
        await StorageRepository.store_metadata(db, file_metadata, user_id, category.value)
        return file_metadata

    @staticmethod
    async def upload_file_to_gcs(file: UploadFile, 
                                 category: FileCategory,
                                 bucket_name: str = None) -> dict:
        """Upload file to Google Cloud Storage"""
        bucket_name = bucket_name or settings.GCS_BUCKET_NAME
        if not bucket_name:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GCS bucket name is not configured."
            )
        
        try:
            file.file.seek(0)

            loop = asyncio.get_event_loop()
            
            def _upload():
                client = storage.Client()
                bucket = client.bucket(bucket_name)
                blob_name = f"{category.value}/{uuid.uuid4()}_{file.filename}"
                blob = bucket.blob(blob_name)
                blob.upload_from_file(file.file, content_type=file.content_type)
                return blob_name
            
            blob_name = await loop.run_in_executor(None, _upload)
            
            # Generate signed URL for the uploaded file
            url = await StorageService.generate_signed_url(bucket_name, blob_name)

            # Get file size
            file.file.seek(0, 2)  
            size = file.file.tell()
            file.file.seek(0)

            return {
                "url": url,
                "blob_name": blob_name,
                "content_type": file.content_type,
                "filename": file.filename,
                "bucket": bucket_name,
                "size": size
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Unexpected error uploading file to GCS: {str(e)}"
            )
        
    @staticmethod
    async def delete_file(db: AsyncSession,
                         blob_name: str,
                         bucket_name: str = None) -> dict:
        """Delete file from GCS and remove metadata from database"""
        bucket_name = bucket_name or settings.GCS_BUCKET_NAME
        if not bucket_name:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GCS bucket name is not configured."
            )
        
        try:
            # Delete from GCS
            loop = asyncio.get_event_loop()
            
            def _delete():
                client = storage.Client()
                bucket = client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                blob.delete()
            
            await loop.run_in_executor(None, _delete)
            
            # Delete metadata from database
            await StorageRepository.delete_metadata_by_blob_name(db, blob_name)

            return {"detail": "File deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Unexpected error deleting file from GCS: {str(e)}"
            )

    @staticmethod
    async def get_file_url(blob_name: str,
                          bucket_name: str = None) -> str:
        """Get signed URL for a file in GCS"""
        bucket_name = bucket_name or settings.GCS_BUCKET_NAME
        if not bucket_name:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GCS bucket name is not configured."
            )
        
        try:
            return await StorageService.generate_signed_url(bucket_name, blob_name)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Unexpected error retrieving file URL from GCS: {str(e)}"
            )
        

    @staticmethod
    async def generate_signed_url(bucket_name: str, 
                                  blob_name: str, 
                                  expiration_seconds: int = 3600) -> str:
        """Generate a signed URL for accessing a file in GCS"""
        try:
            loop = asyncio.get_event_loop()
            
            def _generate():
                client = storage.Client()
                bucket = client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                return blob.generate_signed_url(
                    expiration=timedelta(seconds=expiration_seconds), 
                    version="v4"
                )
            
            return await loop.run_in_executor(None, _generate)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate signed URL: {str(e)}"
            )
            
    @staticmethod
    async def get_metadata_by_user_id(db: AsyncSession, user_id: int) -> list[FileMetadataResponse]:
        """Get all file metadata for a specific user"""
        try:
            metadata_list = await StorageRepository.get_metadata_by_user_id(db, user_id)
            return [FileMetadataResponse.model_validate(metadata) for metadata in metadata_list]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving metadata by user ID: {str(e)}"
            )