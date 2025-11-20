from fastapi import APIRouter, Depends, Path, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from database.db import get_db
from services.storage_service import StorageService
from models.metadata import *
from schemas.storage_schema import *
from utils.token.authentication_util import get_current_user

router = APIRouter(prefix="/storage", tags=["Storage"])

@router.get("/files", response_model=list[FileMetadataResponse], status_code=status.HTTP_200_OK)
async def get_user_files_metadata(
    filters: FileMetadataFilter,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await StorageService.get_user_files(db, current_user["user_id"], filters)

@router.get("/files/{blob_name:path}", response_model=FileMetadataResponse, status_code=status.HTTP_200_OK)
async def get_file_metadata(
    blob_name: str = Path(..., description="The blob name/path of the file"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await StorageService.get_file_by_blob_name(db, current_user["user_id"], blob_name)

@router.post("/files", response_model=FileMetadataResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    category: FileCategory,
    file: UploadFile = File(...),
    bucket_name: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await StorageService.upload_file(db, file, current_user["user_id"], category, bucket_name)

@router.delete("/files/{blob_name:path}", status_code=status.HTTP_200_OK)  # Changed from /delete/
async def delete_file(
    blob_name: str = Path(...),
    bucket_name: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await StorageService.delete_file(db, current_user["user_id"],  blob_name, bucket_name)

