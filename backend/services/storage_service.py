from fastapi import File, UploadFile, HTTPException
from google.cloud import storage
from sqlalchemy.ext.asyncio import AsyncSession
from backend.utils.config import settings
from backend.repository.storage_repository import StorageRepository
import uuid
from datetime import timedelta
import asyncio

"""
    Other improvements for future:
    - Add caching for signed URLs to reduce generation overhead
    - File type validation
    - Max file size check 
"""

class StorageService:
    @staticmethod
    async def upload_file(db: AsyncSession,
                          file: UploadFile = File(...), 
                          user_id: str = None, bucket_name: str = None) -> dict:
        if user_id is None:
            raise HTTPException(status_code=400, detail="User ID must be provided for file upload.")
        
        file_metadata = await StorageService.upload_file_to_gcs(file, bucket_name)
        
        # await the async repository call
        await StorageRepository.store_metadata(db, file_metadata, user_id)
        return file_metadata

    @staticmethod
    async def upload_file_to_gcs(file: UploadFile = File(...), 
                                bucket_name: str = None) -> dict:
        bucket_name = bucket_name or settings.GCS_BUCKET_NAME
        if not bucket_name:
            raise HTTPException(status_code=500, detail="GCS bucket name is not configured.")
        
        try:
            file.file.seek(0)

            # Run blocking GCS operations in thread pool to avoid blocking event loop
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
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload file to GCS: {e}")
        
    @staticmethod
    async def delete_file(db: AsyncSession,
                         bucket_name: str,
                         blob_name: str) -> dict:
        bucket_name = bucket_name or settings.GCS_BUCKET_NAME
        if not bucket_name:
            raise HTTPException(status_code=500, detail="GCS bucket name is not configured.")
        
        try:
            # Run blocking delete in thread pool
            loop = asyncio.get_event_loop()
            
            def _delete():
                client = storage.Client()
                bucket = client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                blob.delete()
            
            await loop.run_in_executor(None, _delete)
            
            # await the async repository call
            await StorageRepository.delete_metadata_by_blob_name(db, blob_name)

            return {"detail": "File deleted successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete file from GCS: {e}")

    @staticmethod
    async def get_file_url(bucket_name: str, 
                          blob_name: str) -> str:
        bucket_name = bucket_name or settings.GCS_BUCKET_NAME
        if not bucket_name:
            raise HTTPException(status_code=500, detail="GCS bucket name is not configured.")
        
        try:
            return await StorageService.generate_signed_url(bucket_name=bucket_name, blob_name=blob_name)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get file URL from GCS: {e}")
        

    @staticmethod
    async def generate_signed_url(bucket_name: str, blob_name: str, expiration_seconds: int = 3600) -> str:
        try:
            # Run blocking signed URL generation in thread pool
            loop = asyncio.get_event_loop()
            
            def _generate():
                client = storage.Client()
                bucket = client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                return blob.generate_signed_url(expiration=timedelta(seconds=expiration_seconds), version="v4")
            
            return await loop.run_in_executor(None, _generate)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate signed URL: {e}")