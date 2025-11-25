from services.map_service import mapService
from schemas.air_schema import AirQualityResponse
from fastapi import HTTPException, status
from integration.air_api import create_air_quality_client 
from schemas.destination_schema import Location

class AirService:         
    @staticmethod
    async def get_air_quality(place_id: str) -> AirQualityResponse:
        try:
            try:
                detail = await mapService.get_location_details(place_id)
                location = detail.geometry.location
                air_client = await create_air_quality_client()
                return await air_client.get_air_quality(location=location)
            finally:
                if air_client:
                    await air_client.close()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get air quality data: {str(e)}"
            )