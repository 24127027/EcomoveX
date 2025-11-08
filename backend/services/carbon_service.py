from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from integration.climatiq_api import create_climatiq_client
from typing import Optional
from models.route import TransportMode

class CarbonService:
    @staticmethod
    async def estimate_transport_emission(
        mode: TransportMode,
        distance_km: float,
        passengers: int = 1,
        fuel_type: Optional[str] = None
    ):
        try:
            climatiq = await create_climatiq_client()
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
        finally:
            await climatiq.close()