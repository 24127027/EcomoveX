from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.map_schema import Location
from database.db import get_db
from services.recommendation_service import RecommendationService
from utils.token.authentication_util import get_current_user

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/user/me", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def get_recommendations_for_current_user(
    k: int = Query(default=10, ge=1, le=50),
    use_hybrid: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await RecommendationService.recommend_for_user(
        db, current_user["user_id"], k=k, use_hybrid=use_hybrid
    )


@router.post(
    "/user/me/sort-by-cluster",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Sort recommendations by user's cluster affinity",
)
async def sort_recommendations_by_cluster_affinity(
    recommendations: List[Dict[str, Any]],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Sort a list of recommendations based on how well they match the current user's cluster preferences.

    Request body should contain a list of recommendation items with at least 'destination_id' field.
    Returns the same list sorted by cluster affinity score (descending).
    """
    return await RecommendationService.sort_recommendations_by_user_cluster_affinity(
        db=db,
        user_id=current_user["user_id"],
        recommendations=recommendations,
    )


@router.post(
    "/user/{user_id}/sort-by-cluster",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Sort recommendations by user's cluster affinity (by user_id)",
)
async def sort_recommendations_by_cluster_affinity_for_user(
    user_id: int,
    recommendations: List[Dict[str, Any]],
    db: AsyncSession = Depends(get_db),
):
    """
    Sort a list of recommendations based on how well they match a specific user's cluster preferences.

    Request body should contain a list of recommendation items with at least 'destination_id' field.
    Returns the same list sorted by cluster affinity score (descending).
    """
    return await RecommendationService.sort_recommendations_by_user_cluster_affinity(
        db=db,
        user_id=user_id,
        recommendations=recommendations,
    )


@router.get(
    "/user/me/nearby-by-cluster",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get nearby recommendations based on user's cluster preferences",
)
async def get_nearby_recommendations_by_cluster_tags(
    latitude: float = Query(..., description="Current latitude", ge=-90, le=90),
    longitude: float = Query(..., description="Current longitude", ge=-180, le=180),
    radius_km: float = Query(default=5.0, description="Search radius in kilometers", ge=0.1, le=50),
    k: int = Query(default=10, description="Number of recommendations", ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get nearby destination recommendations based on current user's cluster preferences.

    Uses the user's cluster to determine preferred place categories and searches for nearby places
    matching those preferences within the specified radius.

    Returns a list of places with scores based on:
    - Proximity to current location
    - Place rating
    - Number of reviews
    - Match with cluster preferences
    """
    from schemas.destination_schema import Location

    current_location = Location(lat=latitude, lng=longitude)

    return await RecommendationService.recommend_nearby_by_cluster_tags(
        db=db,
        user_id=current_user["user_id"],
        current_location=current_location,
        radius_km=radius_km,
        k=k,
    )


@router.get(
    "/user/{user_id}/nearby-by-cluster",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get nearby recommendations based on user's cluster preferences (by user_id)",
)
async def get_nearby_recommendations_by_cluster_tags_for_user(
    user_id: int,
    latitude: float = Query(..., description="Current latitude", ge=-90, le=90),
    longitude: float = Query(..., description="Current longitude", ge=-180, le=180),
    radius_km: float = Query(default=5.0, description="Search radius in kilometers", ge=0.1, le=50),
    k: int = Query(default=10, description="Number of recommendations", ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Get nearby destination recommendations based on a specific user's cluster preferences.

    Uses the user's cluster to determine preferred place categories and searches for nearby places
    matching those preferences within the specified radius.

    Returns a list of places with scores based on:
    - Proximity to current location
    - Place rating
    - Number of reviews
    - Match with cluster preferences
    """
    from schemas.destination_schema import Location

    current_location = Location(lat=latitude, lng=longitude)

    return await RecommendationService.recommend_nearby_by_cluster_tags(
        db=db,
        user_id=user_id,
        current_location=current_location,
        radius_km=radius_km,
        k=k,
    )

