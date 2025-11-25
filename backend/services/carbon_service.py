from fastapi import HTTPException, status
from integration.carbon_api import create_carbonAPI_client
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
            carbonAPI = await create_carbonAPI_client()
            estimation = await carbonAPI.estimate_transport(
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
            if carbonAPI:
                await carbonAPI.close()