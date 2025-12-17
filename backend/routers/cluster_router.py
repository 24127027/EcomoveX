from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict

from database.db import get_db
from utils.token.authentication_util import get_current_user
from schemas.cluster_schema import ClusteringResultResponse
from services.cluster_service import ClusterService

router = APIRouter(prefix="/clustering", tags=["clustering"])


@router.post("/run", response_model=ClusteringResultResponse, status_code=status.HTTP_200_OK)
async def trigger_clustering(db: AsyncSession = Depends(get_db)):
    return await ClusterService.run_user_clustering(db)


@router.get("/preference-exists",response_model=bool ,status_code=status.HTTP_200_OK)
async def check_user_preference_exists(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await ClusterService.is_user_have_preference(db, current_user["user_id"])


@router.put("/preference", status_code=status.HTTP_200_OK)
async def update_user_preference(
    preference_data: Dict = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await ClusterService.update_preference(
        db, current_user["user_id"], preference_data
    )
