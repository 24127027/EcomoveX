from fastapi import APIRouter, Depends, Path, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from database.db import get_db
from services.storage_service import StorageService
from models.metadata import *
from schemas.storage_schema import *
from utils.token.authentication_util import get_current_user

router = APIRouter(prefix="/storage", tags=["Storage"])

@router.get("/me", response_model=list[FileMetadataResponse], status_code=status.HTTP_200_OK)
async def get_metadata_by_user_id(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await StorageService.get_metadata_by_user_id(db, current_user["user_id"])

@router.post("/upload", response_model=FileMetadataResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    category: FileCategory,
    file: UploadFile = File(...),
    bucket_name: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await StorageService.upload_file(db, file, current_user["user_id"], category, bucket_name)

@router.delete("/delete/{blob_name:path}", status_code=status.HTTP_200_OK)
async def delete_file(
    blob_name: str = Path(...),
    bucket_name: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await StorageService.delete_file(db, blob_name, bucket_name)