from fastapi import APIRouter, Depends
from database.db import get_db
from services.cluster_service import ClusterService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/clustering", tags=["clustering"])

@router.post("/run")
async def trigger_clustering(
    db: AsyncSession = Depends(get_db)
):
    return await ClusterService.run_user_clustering(db)