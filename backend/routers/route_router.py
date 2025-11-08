from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.user_database import get_user_db
from services.route_service import RouteService
from schemas.route_schema import FindRoutesRequest, FindRoutesResponse, RouteCreate, RouteResponse
from utils.authentication_util import get_current_user
from typing import List

router = APIRouter(prefix="/routes", tags=["Routes"])

@router.post(
    "/find-optimal",
    response_model=FindRoutesResponse,
)
async def find_optimal_routes(
    request: FindRoutesRequest,
    current_user: dict = Depends(get_current_user)
):
    return await RouteService.find_three_optimal_routes(request)