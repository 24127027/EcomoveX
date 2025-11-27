from services.map_service import MapService
from schemas.air_schema import AirQualityResponse
from schemas.map_schema import PlaceDetailsRequest, PlaceDataCategory
from fastapi import HTTPException, status
from integration.air_api import create_air_quality_client 
from schemas.destination_schema import Location

class AirService:         
    @staticmethod
    async def get_air_quality(place_id: str) -> AirQualityResponse:
        air_client = None
        try:
            request_data = PlaceDetailsRequest(
                place_id=place_id,
                categories=[PlaceDataCategory.BASIC]
            )
            detail = await MapService.get_location_details(request_data)
            location = detail.geometry.location
            air_client = await create_air_quality_client()
            return await air_client.get_air_quality(location=location)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get air quality data: {str(e)}"
            )
        finally:
            if air_client:
                await air_client.close()