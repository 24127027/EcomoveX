from fastapi import APIRouter, status
from schemas.route_schema import *
from services.route_service import RouteService

router = APIRouter(prefix="/routes", tags=["Routes"])


@router.post(
    "/find-optimal", response_model=FindRoutesResponse, status_code=status.HTTP_200_OK
)
async def find_optimal_routes(request: FindRoutesRequest):
    return await RouteService.find_three_optimal_routes(request)
