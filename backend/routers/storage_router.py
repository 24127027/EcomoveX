from fastapi import APIRouter, Depends, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.user_database import get_user_db
from services.storage_service import StorageService
from models.metadata import *
from schemas.storage_schema import *
from utils.token.authentication_util import get_current_user

router = APIRouter(prefix="/storage", tags=["Storage"])

@router.get("/{bucket_name}/me", response_model= list[FileMetadataResponse], status_code=status.HTTP_200_OK)
async def get_metadata_by_user_id(
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await StorageService.get_metadata_by_user_id(db, current_user["user_id"])

@router.post("/{bucket_name}/upload", response_model=FileMetadataResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    db: AsyncSession = Depends(get_user_db),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    bucket_name: str = Query(None)
):
    return await StorageService.upload_file(db, file, current_user["user_id"], bucket_name)

@router.delete("/{bucket_name}/delete/{blob_name}", status_code=status.HTTP_200_OK)
async def delete_file(
    db: AsyncSession = Depends(get_user_db),
    blob_name: str = Query(...),
    bucket_name: str = Query(...)
):
    return await StorageService.delete_file(db, bucket_name, blob_name)