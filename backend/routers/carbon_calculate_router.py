# carbon_calculate_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# Assuming these imports exist relative to your project structure
from .carbon_calculate_schema import CarbonCalculateRequest, CarbonCalculateResponse
from .carbon_calculate_service import CarbonCalculateService # We'll fill this in next!
from ..database import get_db # Assuming get_db is accessible like this

router = APIRouter(
    prefix="/carbon-footprint", # All endpoints in this router start with /carbon-footprint
    tags=["Carbon Footprint"],
)

@router.post("/calculate", response_model=CarbonCalculateResponse)
async def calculate_carbon_footprint_endpoint(
    request_data: CarbonCalculateRequest,
    db: AsyncSession = Depends(get_db) # Inject database session
):
    # This is where the router calls the service to do the actual work
    try:
        service = CarbonCalculateService(db) # Pass db session to service
        carbon_emission = await service.calculate_single_trip_emission(
            vehicle_type=request_data.vehicle_type,
            distance_km=request_data.distance_km,
            fuel_type=request_data.fuel_type
        )
        return CarbonCalculateResponse(
            vehicle_type=request_data.vehicle_type,
            distance_km=request_data.distance_km,
            fuel_type=request_data.fuel_type,
            carbon_emission_kg=carbon_emission
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")