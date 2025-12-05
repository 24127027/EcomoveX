from fastapi import APIRouter, Query, status
from schemas.route_schema import TransportMode
from services.carbon_service import CarbonService
from schemas.carbon_schemas import EmissionRequest

router = APIRouter(prefix="/carbon", tags=["Carbon Emissions Estimation"])


"""
    Estimate carbon emission for a given transport mode, per passenger.
    Returns the estimated carbon emission in kg CO2e.

"""
@router.post("/estimate", response_model=float)
async def estimate_transport_emission(req: EmissionRequest):
    carbon_emission = await CarbonService.estimate_transport_emission(
        req.transport_mode, req.distance_km, req.passengers
    )
    return carbon_emission
