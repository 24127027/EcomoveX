from fastapi import APIRouter, Depends, status
from database.db import get_db
from services.cluster_service import ClusterService
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

router = APIRouter(prefix="/clustering", tags=["clustering"])


@router.post("/run", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def trigger_clustering(db: AsyncSession = Depends(get_db)):
    return await ClusterService.run_user_clustering(db)
