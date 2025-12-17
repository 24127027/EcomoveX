from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db
from schemas.recommendation_schema import SimpleRecommendation
from services.recommendation_service import RecommendationService
from utils.token.authentication_util import get_current_user

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get(
    "/user/me", response_model=List[SimpleRecommendation], status_code=status.HTTP_200_OK
)
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
    "/user/me/cluster-affinity",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get destination IDs based on cluster affinity",
)
async def get_cluster_affinity_recommendations(
    k: int = Query(default=5, description="Number of recommendations to return", ge=1, le=50),
    include_scores: bool = Query(default=False, description="Include affinity/popularity scores in response"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get personalized destination recommendations from internal database based on cluster affinity.
    
    **Returns destination IDs** that are already stored in the database and associated with
    the user's cluster, ranked by relevance.
    
    **Algorithm:**
    1. Identifies user's cluster
    2. Computes cluster embedding (mean of user preferences)
    3. Fetches destinations already linked to that cluster
    4. Calculates affinity via cosine similarity: cluster_embedding ↔ destination_embedding
    5. Combines affinity (70%) + popularity (30%) based on historical user behavior
    6. Returns top-K destination IDs
    
    **Response (include_scores=False):**
    ```json
    [
      {"destination_id": "ChIJAbC123..."},
      {"destination_id": "ChIJXyz789..."}
    ]
    ```
    
    **Response (include_scores=True):**
    ```json
    [
      {
        "destination_id": "ChIJAbC123...",
        "affinity_score": 0.8542,
        "popularity_score": 78.5,
        "combined_score": 0.8334
      }
    ]
    ```
    
    **Use Cases:**
    - Get destination IDs for homepage recommendations
    - Fetch IDs, then query place details separately via /map/place-details endpoint
    - Personalized discovery based on similar users' behavior
    """
    return await RecommendationService.recommend_destinations_by_cluster_affinity(
        db=db,
        user_id=current_user["user_id"],
        k=k,
        include_scores=include_scores,
    )


@router.get(
    "/user/{user_id}/cluster-affinity",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get destination IDs based on cluster affinity (by user_id)",
)
async def get_cluster_affinity_recommendations_for_user(
    user_id: int,
    k: int = Query(default=5, description="Number of recommendations to return", ge=1, le=50),
    include_scores: bool = Query(default=False, description="Include affinity/popularity scores in response"),
    db: AsyncSession = Depends(get_db),
):
    
    
    return await RecommendationService.recommend_destinations_by_cluster_affinity(
        db=db,
        user_id=user_id,
        k=k,
        include_scores=include_scores,
    )
