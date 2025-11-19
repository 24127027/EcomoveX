from schemas.air_schema import AirQualityResponse
from fastapi import HTTPException, status
from typing import Tuple
from integration.air_api import create_air_quality_client 

class AirService:         
    @staticmethod
    async def get_air_quality(location: Tuple[float, float]) -> AirQualityResponse:
        try:
            try:
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