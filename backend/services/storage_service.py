from fastapi import File, UploadFile, HTTPException
from google.cloud import storage
from sqlalchemy.ext.asyncio import AsyncSession
from utils.config import settings
import uuid
from datetime import timedelta

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

        from repository.storage_repository import StorageRepository
        StorageRepository.store_metadata(db, file_metadata, user_id)
        return file_metadata

    @staticmethod
    async def upload_file_to_gcs(db: AsyncSession,
                                file: UploadFile = File(...), 
                                bucket_name: str = None) -> dict:
        bucket_name = bucket_name or settings.GCS_BUCKET_NAME
        if not bucket_name:
            raise HTTPException(status_code=500, detail="GCS bucket name is not configured.")
        
        try:
            file.file.seek(0)

            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob_name = f"{uuid.uuid4()}_{file.filename}"
            blob = bucket.blob(blob_name)
            
            blob.upload_from_file(file.file, content_type=file.content_type)

            url = StorageService.generate_signed_url(bucket_name, blob_name)

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
    def delete_file(db: AsyncSession,
                    bucket_name: str,
                    blob_name: str) -> dict:
        bucket_name = bucket_name or settings.GCS_BUCKET_NAME
        if not bucket_name:
            raise HTTPException(status_code=500, detail="GCS bucket name is not configured.")
        
        try:
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.delete()
            return {"detail": "File deleted successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete file from GCS: {e}")

    @staticmethod
    def get_file_url(bucket_name: str, 
                     blob_name: str) -> str:
        # Use configured default bucket if none supplied
        bucket_name = bucket_name or settings.GCS_BUCKET_NAME
        if not bucket_name:
            raise HTTPException(status_code=500, detail="GCS bucket name is not configured.")
        
        try:
            # Return a signed URL (safe for private buckets). If your bucket is public
            # you can return blob.public_url instead.
            return StorageService.generate_signed_url(bucket_name=bucket_name, blob_name=blob_name)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get file URL from GCS: {e}")
        

    @staticmethod
    def generate_signed_url(bucket_name: str, blob_name: str, expiration_seconds: int = 3600) -> str:
        try:
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            return blob.generate_signed_url(expiration=timedelta(seconds=expiration_seconds))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate signed URL: {e}")