from fastapi import APIRouter, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.route_schema import TransportMode
from services.carbon_service import CarbonService

router = APIRouter(prefix="/carbon", tags=["Carbon Emissions Estimation"])


"""
    Estimate carbon emission for a given transport mode, per passenger.
    Returns the estimated carbon emission in kg CO2e.
"""
@router.post("/estimate", response_model=dict, status_code=status.HTTP_200_OK)
async def estimate_transport_emission(transport_mode: TransportMode = Query(),
                                    distance_km: float = Query(),
                                    passengers: int = Query(1)):
    carbon_emission = await CarbonService.estimate_transport_emission(transport_mode, distance_km, passengers)
    return carbon_emission
