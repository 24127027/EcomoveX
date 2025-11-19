from fastapi import HTTPException, status
from integration.climatiq_api import create_climatiq_client
from typing import Optional
from schemas.route_schema import TransportMode

class CarbonService:
    @staticmethod
    async def estimate_transport_emission(
        mode: TransportMode,
        distance_km: float,
        passengers: int = 1,
    ):
        try:
            climatiq = await create_climatiq_client()
            estimation = await climatiq.estimate_transport(
                mode=mode,
                distance_km=distance_km,
                passengers=passengers,
            )
            return estimation
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error estimating transport emission: {e}"
            )
        finally:
            await climatiq.close()