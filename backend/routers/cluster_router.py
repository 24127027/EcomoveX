from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict

from database.db import get_db
from utils.token.authentication_util import get_current_user
from schemas.cluster_schema import ClusteringResultResponse, PreferenceUpdate
from services.cluster_service import ClusterService

router = APIRouter(prefix="/clustering", tags=["clustering"])


@router.post("/run", response_model=ClusteringResultResponse, status_code=status.HTTP_200_OK)
async def trigger_clustering(db: AsyncSession = Depends(get_db)):
    return await ClusterService.run_user_clustering(db)


@router.get("/preference-exists",response_model=bool ,status_code=status.HTTP_200_OK)
async def check_user_preference_exists(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await ClusterService.is_user_have_preference(db, current_user["user_id"])


@router.put("/preference", status_code=status.HTTP_200_OK)
async def update_user_preference(
    preference_data: Dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Convert frontend format to backend format
    climate_to_temp = {
        "warm": {"min_temp": 25, "max_temp": 35},
        "cool": {"min_temp": 15, "max_temp": 25},
        "cold": {"min_temp": 0, "max_temp": 15},
        "any": {"min_temp": 0, "max_temp": 40}
    }
    
    budget_to_range = {
        "low": {"min": 0.0, "max": 500000.0},
        "mid": {"min": 500000.0, "max": 2000000.0},
        "luxury": {"min": 2000000.0, "max": 10000000.0}
    }
    
    weather_pref = None
    if preference_data.get("weather_pref"):
        climate = preference_data["weather_pref"].get("climate", "any")
        weather_pref = climate_to_temp.get(climate, climate_to_temp["any"])
    
    budget_range = None
    if preference_data.get("budget_range"):
        level = preference_data["budget_range"].get("level", "mid")
        budget_range = budget_to_range.get(level, budget_to_range["mid"])
    
    data = PreferenceUpdate(
        weather_pref=weather_pref,
        attraction_types=preference_data.get("attraction_types"),
        budget_range=budget_range,
        kids_friendly=preference_data.get("kids_friendly", False)
    )
    
    return await ClusterService.update_preference(
        db, current_user["user_id"], data
    )