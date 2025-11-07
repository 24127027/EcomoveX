from fastapi import APIRouter, Depends, HTTPException, status, Query
from backend.schemas.route_schema import (
    RouteRequest, 
    CompareRoutesRequest, 
    EcoRouteRequest,
    OptimalRoutesResponse,
    CompareRoutesResponse,
    EcoRouteResponse
)
from services.map_service import MapService
from utils.authentication_util import get_current_user
from typing import Dict, Any

router = APIRouter(prefix="/map", tags=["Map & Routing"])

@router.post("/optimal-routes", status_code=status.HTTP_200_OK)
async def find_optimal_routes(
    request: RouteRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Find 3 optimal routes between origin and destination:
    - Fastest route
    - Lowest carbon emissions route
    - Smart combination route (balance between time and carbon)
    """
    try:
        result = await MapService.find_three_optimal_routes(
            origin=request.origin,
            destination=request.destination,
            max_time_ratio=request.max_time_ratio,
            language=request.language
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find optimal routes: {str(e)}"
        )

@router.post("/compare-routes", status_code=status.HTTP_200_OK)
async def compare_all_routes(
    request: CompareRoutesRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Compare all available route options (driving, walking, bicycling, transit)
    with detailed carbon emission calculations and recommendations.
    """
    try:
        result = await MapService.compare_all_route_options(
            origin=request.origin,
            destination=request.destination,
            max_time_ratio=request.max_time_ratio
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare routes: {str(e)}"
        )

@router.post("/eco-route", status_code=status.HTTP_200_OK)
async def calculate_eco_friendly_route(
    request: EcoRouteRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate eco-friendly driving route avoiding highways and tolls
    with carbon emission estimation.
    """
    try:
        result = await MapService.calculate_eco_route(
            origin=request.origin,
            destination=request.destination,
            avoid_highways=request.avoid_highways,
            avoid_tolls=request.avoid_tolls
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate eco route: {str(e)}"
        )

@router.get("/emission-factors", status_code=status.HTTP_200_OK)
async def get_emission_factors(
    current_user: dict = Depends(get_current_user)
):
    """
    Get all available emission factors for different transportation modes
    in Vietnam (gCO2/km per passenger).
    """
    try:
        from services.carbon_service import CarbonService
        factors = CarbonService.get_all_emission_factors()
        
        return {
            "emission_factors": factors,
            "unit": "gCO2/km per passenger",
            "country": "Vietnam",
            "data_sources": ["Climatiq", "IPCC 2019", "Electricity Maps"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve emission factors: {str(e)}"
        )

@router.post("/refresh-emission-factors", status_code=status.HTTP_200_OK)
async def refresh_emission_factors(
    force: bool = Query(False, description="Force refresh even if recently updated"),
    current_user: dict = Depends(get_current_user)
):
    """
    Refresh emission factors from Climatiq API.
    Use force=true to bypass cache and get latest data.
    """
    try:
        from services.carbon_service import CarbonService
        factors = await CarbonService.refresh_emission_factors(force=force)
        
        return {
            "message": "Emission factors refreshed successfully",
            "emission_factors": factors,
            "unit": "gCO2/km per passenger",
            "country": "Vietnam"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh emission factors: {str(e)}"
        )

@router.get("/calculate-carbon", status_code=status.HTTP_200_OK)
async def calculate_route_carbon(
    distance_km: float = Query(..., gt=0, description="Distance in kilometers"),
    mode: str = Query(..., description="Transportation mode (driving, walking, bicycling, transit, etc.)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate carbon emissions for a specific distance and transportation mode.
    """
    try:
        result = await MapService.calculate_route_carbon(
            distance_km=distance_km,
            mode=mode
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate carbon emissions: {str(e)}"
        )
