from fastapi import File, UploadFile, HTTPException, status
from google.cloud import storage
from sqlalchemy.ext.asyncio import AsyncSession
from utils.config import settings
from repository.storage_repository import StorageRepository
import uuid
from datetime import timedelta
import asyncio
from models.metadata import *
from schemas.storage_schema import *

class StorageService:
    @staticmethod
    async def upload_file(db: AsyncSession,
                          file: UploadFile = File(...), 
                          user_id: str = None, 
                          bucket_name: str = None) -> FileMetadataResponse:
        try:
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User ID is required for file upload"
                )
            
            file_metadata = await StorageService.upload_file_to_gcs(file, bucket_name)
            
            await StorageRepository.store_metadata(db, user_id, file_metadata)
            return file_metadata
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error uploading file: {e}")

    @staticmethod
    async def upload_file_to_gcs(file: UploadFile = File(...), 
                                bucket_name: str = None) -> FileMetadataResponse:
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
                blob_name = f"{uuid.uuid4()}_{file.filename}"
                blob = bucket.blob(blob_name)
                blob.upload_from_file(file.file, content_type=file.content_type)
                return blob_name
            
            blob_name = await loop.run_in_executor(None, _upload)
            
            url = await StorageService.generate_signed_url(bucket_name, blob_name)

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
                detail=f"Unexpected error uploading file to GCS: {e}")
        
    @staticmethod
    async def delete_file(db: AsyncSession,
                         bucket_name: str,
                         blob_name: str):
        try:
            bucket_name = bucket_name or settings.GCS_BUCKET_NAME
            if not bucket_name:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                    detail="GCS bucket name is not configured"
                )
            
            loop = asyncio.get_event_loop()
            
            def _delete():
                client = storage.Client()
                bucket = client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                blob.delete()
            
            await loop.run_in_executor(None, _delete)
            
            await StorageRepository.delete_metadata_by_blob_name(db, blob_name)

            return {"detail": "File deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Unexpected error deleting file from GCS: {e}")

    @staticmethod
    async def get_file_url(bucket_name: str, 
                          blob_name: str) -> str:
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
                detail=f"Unexpected error retrieving file URL from GCS: {e}"
            )
        

    @staticmethod
    async def generate_signed_url(bucket_name: str, 
                                 blob_name: str, 
                                 expiration_seconds: int = 3600) -> str:
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
                detail=f"Unexpected error generating signed URL: {e}"
            )
            
    @staticmethod
    async def get_metadata_by_user_id(db: AsyncSession, user_id: int) -> list[FileMetadataResponse]:
        try:
            metadata_list = await StorageRepository.get_metadata_by_user_id(db, user_id)
            return metadata_list
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving metadata by user ID: {e}"
            )