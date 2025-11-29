import asyncio
import uuid
from datetime import timedelta

from fastapi import HTTPException, UploadFile, status
from google.cloud import storage
from sqlalchemy.ext.asyncio import AsyncSession

from repository.storage_repository import StorageRepository
from schemas.storage_schema import (
    FileCategory,
    FileMetadata,
    FileMetadataFilter,
    FileMetadataResponse,
    MetadataCreate,
)
from utils.config import settings


class StorageService:
    @staticmethod
    async def upload_file(
        db: AsyncSession,
        file: UploadFile,
        user_id: int,
        category: FileCategory,
        bucket_name: str = None,
    ) -> FileMetadataResponse:
        try:
            file_metadata = await StorageService.upload_file_to_gcs(file, category, bucket_name)

            metadata_create = MetadataCreate(
                blob_name=file_metadata.blob_name,
                user_id=user_id,
                filename=file_metadata.filename,
                content_type=file_metadata.content_type,
                category=category.value,
                bucket=file_metadata.bucket,
                size=file_metadata.size,
            )
            stored_metadata = await StorageRepository.store_metadata(db, metadata_create)

            if not stored_metadata:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to store file metadata in database",
                )

            return FileMetadataResponse(
                url=file_metadata.url,
                blob_name=file_metadata.blob_name,
                filename=file_metadata.filename,
                content_type=file_metadata.content_type,
                category=category.value,
                size=file_metadata.size,
                updated_at=stored_metadata.uploaded_at,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error uploading file: {str(e)}",
            )

    @staticmethod
    async def upload_file_to_gcs(
        file: UploadFile, category: FileCategory, bucket_name: str = None
    ) -> FileMetadata:
        try:
            bucket_name = bucket_name or settings.GCS_BUCKET_NAME
            if not bucket_name:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="GCS bucket name is not configured",
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

            url = await StorageService.generate_signed_url(blob_name, bucket_name)

            file.file.seek(0, 2)
            size = file.file.tell()
            file.file.seek(0)

            return FileMetadata(
                url=url,
                blob_name=blob_name,
                content_type=file.content_type,
                filename=file.filename,
                bucket=bucket_name,
                size=size,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error uploading file to GCS: {str(e)}",
            )

    @staticmethod
    async def delete_file(
        db: AsyncSession, user_id: int, blob_name: str, bucket_name: str = None
    ) -> dict:
        try:
            bucket_name = bucket_name or settings.GCS_BUCKET_NAME
            if not bucket_name:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="GCS bucket name is not configured",
                )

            metadata = await StorageRepository.get_metadata_by_blob_name(db, user_id, blob_name)
            if not metadata:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found or you don't have permission to delete it",
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
                detail=f"Unexpected error deleting file from GCS: {str(e)}",
            )

    @staticmethod
    async def generate_signed_url(
        blob_name: str, bucket_name: str = None, expiration_seconds: int = 3600
    ) -> str:
        try:
            bucket_name = bucket_name or settings.GCS_BUCKET_NAME
            if not bucket_name:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="GCS bucket name is not configured",
                )

            loop = asyncio.get_event_loop()

            def _generate():
                client = storage.Client()
                bucket = client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                return blob.generate_signed_url(
                    expiration=timedelta(seconds=expiration_seconds), version="v4"
                )

            return await loop.run_in_executor(None, _generate)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error generating signed URL: {str(e)}",
            )

    @staticmethod
    async def get_user_files(
        db: AsyncSession, user_id: int, filters: FileMetadataFilter
    ) -> list[FileMetadataResponse]:
        try:
            metadata_list = await StorageRepository.get_user_files_metadata(db, user_id, filters)

            result = []
            for metadata in metadata_list:
                url = await StorageService.generate_signed_url(metadata.blob_name, metadata.bucket)
                result.append(
                    FileMetadataResponse(
                        url=url,
                        blob_name=metadata.blob_name,
                        filename=metadata.filename,
                        content_type=metadata.content_type,
                        category=metadata.category,
                        size=metadata.size,
                        updated_at=metadata.uploaded_at,
                    )
                )

            return result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving metadata by user ID: {str(e)}",
            )

    @staticmethod
    async def get_file_by_blob_name(
        db: AsyncSession, user_id: int, blob_name: str
    ) -> FileMetadataResponse:
        try:
            metadata = await StorageRepository.get_metadata_by_blob_name(db, user_id, blob_name)

            if not metadata:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

            url = await StorageService.generate_signed_url(metadata.blob_name, metadata.bucket)

            return FileMetadataResponse(
                url=url,
                blob_name=metadata.blob_name,
                filename=metadata.filename,
                content_type=metadata.content_type,
                category=metadata.category,
                size=metadata.size,
                updated_at=metadata.uploaded_at,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving file: {str(e)}",
            )
