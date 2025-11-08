from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from integration.climatiq_api import climatiqAPI
from typing import Optional
class CarbonService:
    @staticmethod
    async def estimate_transport_emission(
        mode: str,
        distance_km: float,
        passengers: int = 1,
        fuel_type: Optional[str] = None
    ):
        try:
            climatiq = climatiqAPI()
            estimation = await climatiq.estimate_transport(
                mode=mode,
                distance_km=distance_km,
                passengers=passengers,
                fuel_type=fuel_type
            )
            return estimation
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error estimating transport emission: {e}"
            )