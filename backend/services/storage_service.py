from fastapi import File, UploadFile, HTTPException
from google.cloud import storage
from fastapi.responses import RedirectResponse
from utils.config import settings
import uuid
from datetime import timedelta

class StorageService:
    @staticmethod
    async def upload_file_to_gcs(file: UploadFile = File(...), bucket_name: str = None) -> dict:
        bucket_name = bucket_name or settings.GCS_BUCKET_NAME
        if not bucket_name:
            raise HTTPException(status_code=500, detail="GCS bucket name is not configured.")
        
        try:
            contents = await file.read()
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob_name = f"{uuid.uuid4()}_{file.filename}"
            blob = bucket.blob(blob_name)
            blob.upload_from_string(contents, content_type=file.content_type)
            url = StorageService.generate_signed_url(bucket_name, blob_name)
            return {
                "url": url,
                "blob_name": blob_name,
                "content_type": file.content_type,
                "filename": file.filename,
                "bucket": bucket_name,
                "size": len(contents)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload file to GCS: {e}")
        
    @staticmethod
    def get_file_url(bucket_name: str, blob_name: str) -> str:
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