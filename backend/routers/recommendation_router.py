from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db
from schemas.recommendation_schema import RecommendationResponse
from services.recommendation_service import RecommendationService
from utils.token.authentication_util import get_current_user

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get(
    "/user/me", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK
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


@router.get(
    "/user/{user_id}",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
async def get_recommendations_for_user(
    user_id: int,
    k: int = Query(default=10, ge=1, le=50),
    use_hybrid: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    return await RecommendationService.recommend_for_user(
        db, user_id, k=k, use_hybrid=use_hybrid
    )


@router.get(
    "/cluster/{cluster_id}/hybrid",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
)
async def get_hybrid_recommendations_for_cluster(
    cluster_id: int,
    k: int = Query(default=20, ge=1, le=100),
    similarity_weight: float = Query(default=0.7, ge=0, le=1),
    popularity_weight: float = Query(default=0.3, ge=0, le=1),
    db: AsyncSession = Depends(get_db),
):
    return await RecommendationService.recommend_for_cluster_hybrid(
        db,
        cluster_id,
        k=k,
        similarity_weight=similarity_weight,
        popularity_weight=popularity_weight,
    )


@router.get(
    "/cluster/{cluster_id}/similarity",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
async def get_similarity_recommendations_for_cluster(
    cluster_id: int,
    k: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    return await RecommendationService.recommend_for_cluster_similarity(
        db, cluster_id, k=k
    )


@router.get(
    "/cluster/{cluster_id}/popularity",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
async def get_popularity_recommendations_for_cluster(
    cluster_id: int, db: AsyncSession = Depends(get_db)
):
    return await RecommendationService.recommend_for_cluster_popularity(db, cluster_id)


@router.get(
    "/user/{user_id}/cluster/{cluster_id}",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
)
async def get_recommendations_based_on_user_cluster(
    user_id: int,
    cluster_id: int,
    k: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    return await RecommendationService.recommend_destination_based_on_user_cluster(
        db, user_id, cluster_id, k=k
    )


@router.get(
    "/me/cluster/{cluster_id}", response_model=List[str], status_code=status.HTTP_200_OK
)
async def get_recommendations_for_current_user_cluster(
    cluster_id: int,
    k: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await RecommendationService.recommend_destination_based_on_user_cluster(
        db, current_user["user_id"], cluster_id, k=k
    )
