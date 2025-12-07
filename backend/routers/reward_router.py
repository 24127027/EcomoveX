from typing import List

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from utils.token.authorizer import require_roles
from database.db import get_db
from schemas.message_schema import CommonMessageResponse
from schemas.reward_schema import (
    MissionCreate,
    MissionResponse,
    MissionUpdate,
    UserRewardResponse,
)
from services.reward_service import RewardService
from utils.token.authentication_util import get_current_user

router = APIRouter(prefix="/rewards", tags=["Rewards & Missions"])


@router.get(
    "/missions/search", response_model=List[MissionResponse], status_code=status.HTTP_200_OK
)
async def search_missions(
    query: str,
    user_db: AsyncSession = Depends(get_db),
):
    return await RewardService.search_missions(user_db, query)


@router.get(
    "/missions", response_model=List[MissionResponse], status_code=status.HTTP_200_OK
)
async def get_all_missions(user_db: AsyncSession = Depends(get_db)):
    return await RewardService.get_all_missions(user_db)


@router.get(
    "/missions/{mission_id}",
    response_model=MissionResponse,
    status_code=status.HTTP_200_OK,
)
async def get_mission_by_id(
    mission_id: int = Path(..., gt=0), user_db: AsyncSession = Depends(get_db)
):
    return await RewardService.get_mission_by_id(user_db, mission_id)


@router.post(
    "/missions",
    dependencies=[Depends(require_roles(["Admin"]))],
    response_model=MissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_mission(
    mission_data: MissionCreate,
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await RewardService.create_mission(user_db, mission_data)


@router.put(
    "/missions/{mission_id}",
    dependencies=[Depends(require_roles(["Admin"]))],
    response_model=MissionResponse,
    status_code=status.HTTP_200_OK,
)
async def update_mission(
    mission_id: int = Path(..., gt=0),
    updated_data: MissionUpdate = ...,
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await RewardService.update_mission(user_db, mission_id, updated_data)


@router.get(
    "/me/missions", response_model=UserRewardResponse, status_code=status.HTTP_200_OK
)
async def get_my_completed_missions(
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await RewardService.all_completed_missions(user_db, current_user["user_id"])


@router.delete(
    "/missions/{mission_id}",
    dependencies=[Depends(require_roles(["Admin"]))],
    response_model=CommonMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_mission(
    mission_id: int = Path(..., gt=0),
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await RewardService.delete_mission(user_db, mission_id)
