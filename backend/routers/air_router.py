from fastapi import APIRouter, Query, status

from schemas.air_schema import AirQualityResponse
from services.air_service import AirService

router = APIRouter(prefix="/air", tags=["Air Quality"])


@router.get("/air-quality", response_model=AirQualityResponse, status_code=status.HTTP_200_OK)
async def get_air_quality(
    place_id: str = Query(...),
):
    return await AirService.get_air_quality(place_id=place_id)
