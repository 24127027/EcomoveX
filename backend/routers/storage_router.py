from fastapi import APIRouter, Depends, Path, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from database.user_database import get_user_db
from services.storage_service import StorageService
from models.metadata import *
from schemas.storage_schema import *
from utils.token.authentication_util import get_current_user

router = APIRouter(prefix="/storage", tags=["Storage"])

@router.get("/files", response_model=list[FileMetadataResponse], status_code=status.HTTP_200_OK)
async def get_user_files_metadata(
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user),
    category: Optional[FileCategory] = Query(None, description="Filter by file category"),
    content_type: Optional[str] = Query(None, description="Filter by MIME type (e.g., 'image/png')"),
    uploaded_after: Optional[datetime] = Query(None, description="Files uploaded after this date"),
    uploaded_before: Optional[datetime] = Query(None, description="Files uploaded before this date"),
    sort_by: FileSortBy = Query(FileSortBy.UPLOADED_AT, description="Field to sort by"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="Sort direction"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    Get user's file metadata with optional filters and pagination.
    
    **Filters:**
    - category: Filter by file category (PROFILE_AVATAR, PROFILE_COVER, TRAVEL_PHOTO)
    - content_type: Filter by MIME type
    - uploaded_after/uploaded_before: Filter by upload date range
    
    **Sorting & Pagination:**
    - sort_by: filename, size, uploaded_at, updated_at
    - sort_order: asc or desc
    - limit: Maximum results per page (1-1000)
    - offset: Number of results to skip
    """
    filters = FileMetadataFilter(
        category=category,
        content_type=content_type,
        uploaded_after=uploaded_after,
        uploaded_before=uploaded_before,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )
    
    return await StorageService.get_user_files(
        db, 
        current_user["user_id"],
        filters
    )

@router.get("/files/{blob_name:path}", response_model=FileMetadataResponse, status_code=status.HTTP_200_OK)
async def get_file_metadata(
    blob_name: str = Path(..., description="The blob name/path of the file"),
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    """Get metadata for a specific file by blob name."""
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
    """Delete a file from cloud storage."""
    return await StorageService.delete_file(
        db, 
        current_user["user_id"],  
        blob_name, 
        bucket_name
    )

