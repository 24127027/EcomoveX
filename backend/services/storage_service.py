from fastapi import File, UploadFile, HTTPException, status
from google.cloud import storage
from sqlalchemy.ext.asyncio import AsyncSession
from utils.config import settings
from repository.storage_repository import StorageRepository
from schemas.storage_schema import FileCategory, FileMetadata, FileMetadataResponse
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
                          ) -> FileMetadataResponse:
        """Upload a file to GCS and store metadata in database"""
        try:
            file_metadata = await StorageService.upload_file_to_gcs(file, category, bucket_name)
            
            # Store metadata in database
            stored_metadata = await StorageRepository.store_metadata(db, user_id, file_metadata, category)
            
            if not stored_metadata:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to store file metadata in database"
                )
            
            return FileMetadataResponse(
                url=file_metadata.url,
                blob_name=file_metadata.blob_name,
                filename=file_metadata.filename,
                content_type=file_metadata.content_type,
                category=category.value,
                size=file_metadata.size,
                updated_at=stored_metadata.uploaded_at if stored_metadata else None
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error uploading file: {str(e)}"
            )

    @staticmethod
    async def upload_file_to_gcs(file: UploadFile, 
                                 category: FileCategory,
                                 bucket_name: str = None) -> FileMetadata:
        """Upload file to Google Cloud Storage"""
        try:
            bucket_name = bucket_name or settings.GCS_BUCKET_NAME
            if not bucket_name:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="GCS bucket name is not configured"
                )
            
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

            return FileMetadata(
                url=url,
                blob_name=blob_name,
                content_type=file.content_type,
                filename=file.filename,
                bucket=bucket_name,
                size=size
            )
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
        try:
            bucket_name = bucket_name or settings.GCS_BUCKET_NAME
            if not bucket_name:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="GCS bucket name is not configured"
                )
            
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
        try:
            bucket_name = bucket_name or settings.GCS_BUCKET_NAME
            if not bucket_name:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="GCS bucket name is not configured"
                )
            
            return await StorageService.generate_signed_url(bucket_name=bucket_name, blob_name=blob_name)
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
                detail=f"Unexpected error generating signed URL: {str(e)}"
            )
            
    @staticmethod
    async def get_metadata_by_user_id(db: AsyncSession, user_id: int) -> list[FileMetadataResponse]:
        """Get all file metadata for a specific user"""
        try:
            metadata_list = await StorageRepository.get_metadata_by_user_id(db, user_id)
            
            # Generate fresh signed URLs for each file
            result = []
            for metadata in metadata_list:
                url = await StorageService.generate_signed_url(metadata.bucket, metadata.blob_name)
                result.append(FileMetadataResponse(
                    url=url,
                    blob_name=metadata.blob_name,
                    filename=metadata.filename,
                    content_type=metadata.content_type,
                    category=metadata.category,
                    size=metadata.size,
                    updated_at=metadata.uploaded_at
                ))
            
            return result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving metadata by user ID: {str(e)}"
            )