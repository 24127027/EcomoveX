from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.user_database import get_user_db
from services.route_service import RouteService
from schemas.route_schema import FindRoutesRequest, FindRoutesResponse, RouteCreate, RouteResponse

router = APIRouter(prefix="/routes", tags=["Routes"])

@router.post(
    "/find-optimal",
    response_model=FindRoutesResponse,
    status_code=status.HTTP_200_OK
)
async def find_optimal_routes(
    request: FindRoutesRequest,
    user_db: AsyncSession = Depends(get_user_db),
):
    return await RouteService.find_three_optimal_routes(request, user_db)