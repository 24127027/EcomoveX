from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from database.user_database import get_user_db
from schemas.reward_schema import MissionCreate, MissionUpdate, MissionResponse, UserRewardResponse
from services.reward_service import RewardService
from utils.authentication_util import get_current_user
from typing import List

router = APIRouter(prefix="/rewards", tags=["Rewards & Missions"])

@router.get("/missions", response_model=List[MissionResponse], status_code=status.HTTP_200_OK)
async def get_all_missions(db: AsyncSession = Depends(get_user_db)):
    return await RewardService.get_all_missions(db)

@router.get("/missions/{mission_id}", response_model=MissionResponse, status_code=status.HTTP_200_OK)
async def get_mission_by_id(
    mission_id: int = Path(..., gt=0, description="Mission ID"),
    db: AsyncSession = Depends(get_user_db)
):
    return await RewardService.get_mission_by_id(db, mission_id)

@router.get("/missions/name/{name}", response_model=MissionResponse, status_code=status.HTTP_200_OK)
async def get_mission_by_name(
    name: str,
    db: AsyncSession = Depends(get_user_db)
):
    return await RewardService.get_mission_by_name(db, name)

@router.post("/missions", response_model=MissionResponse, status_code=status.HTTP_201_CREATED)
async def create_mission(
    mission_data: MissionCreate,
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can create missions"
        )
    return await RewardService.create_mission(db, mission_data)

@router.put("/missions/{mission_id}", response_model=MissionResponse, status_code=status.HTTP_200_OK)
async def update_mission(
    mission_id: int = Path(..., gt=0, description="Mission ID"),
    updated_data: MissionUpdate = ...,
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can update missions"
        )
    return await RewardService.update_mission(db, mission_id, updated_data)

@router.get("/me/missions", status_code=status.HTTP_200_OK)
async def get_my_completed_missions(
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await RewardService.all_completed_missions(db, current_user["user_id"])

@router.get("/users/{user_id}/missions", status_code=status.HTTP_200_OK)
async def get_user_completed_missions(
    user_id: int = Path(..., gt=0, description="User ID"),
    db: AsyncSession = Depends(get_user_db)
):
    return await RewardService.all_completed_missions(db, user_id)

@router.post("/missions/{mission_id}/complete", status_code=status.HTTP_200_OK)
async def complete_mission(
    mission_id: int = Path(..., gt=0, description="Mission ID"),
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await RewardService.complete_mission(db, current_user["user_id"], mission_id)