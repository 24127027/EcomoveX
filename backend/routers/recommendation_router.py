from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query, Body, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db
from services.recommendation_service import RecommendationService
from utils.token.authentication_util import get_current_user

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

@router.post("/sort", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def sort_recommendations_(
    request: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Sort a list of destinations by cluster affinity, popularity, and GPS proximity.
    
    Request body:
    {
        "destination_ids": [1, 2, 3],
        "user_location": {"lat": 10.762622, "lng": 106.660172},  // optional
        "cluster_weight": 0.4,      // optional, default 0.4
        "popularity_weight": 0.3,   // optional, default 0.3
        "proximity_weight": 0.3     // optional, default 0.3
    }
    """
    return await RecommendationService.sort_recommendations_by_place_details(
        db=db,
        user_id=current_user["user_id"],
        request_data=request
    )


@router.get("/nearby", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def get_nearby_recommendations(
    latitude: float = Query(..., description="Current latitude"),
    longitude: float = Query(..., description="Current longitude"),
    radius_km: float = Query(5.0, ge=0.1, le=50, description="Search radius in kilometers"),
    k: int = Query(10, ge=1, le=50, description="Number of recommendations"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get nearby destination recommendations based on user's cluster tags and GPS proximity.
    
    Query Parameters:
    - latitude: Current GPS latitude
    - longitude: Current GPS longitude  
    - radius_km: Search radius in kilometers (default: 5km, max: 50km)
    - k: Number of recommendations to return (default: 10, max: 50)
    """
    return await RecommendationService.recommend_nearby_by_cluster_tags(
        db=db,
        user_id=current_user["user_id"],
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        k=k
    )
    
@router.get("/user/me", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def get_recommendations_for_current_user(
    k: int = Query(default=10, ge=1, le=50),
    use_hybrid: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await RecommendationService.recommend_for_user(
        db, 
        current_user["user_id"], 
        k=k, 
        use_hybrid=use_hybrid
    )
