from fastapi import APIRouter, Query, status
from schemas.air_schema import AirQualityResponse
from schemas.destination_schema import Location
from services.air_service import AirService

router = APIRouter(prefix="/air", tags=["Air Quality"])

@router.get("/air-quality", response_model=AirQualityResponse, status_code=status.HTTP_200_OK)
async def get_air_quality(
    place_id: str = Query(...),
):
    result = await AirService.get_air_quality(place_id=place_id)
    return result