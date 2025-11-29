from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from schemas.message_schema import CommonMessageResponse
from schemas.plan_schema import *
from services.plan_service import PlanService
from utils.token.authentication_util import get_current_user

router = APIRouter(prefix="/plans", tags=["Plans"])


@router.get("/", response_model=List[PlanResponse], status_code=status.HTTP_200_OK)
async def get_plans(
    db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    return await PlanService.get_plans_by_user(db, current_user["user_id"])


@router.post("/", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    plan_data: PlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await PlanService.create_plan(db, current_user["user_id"], plan_data)


@router.put("/{plan_id}", response_model=PlanResponse, status_code=status.HTTP_200_OK)
async def update_plan(
    plan_id: int,
    updated_data: PlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await PlanService.update_plan(db, current_user["user_id"], plan_id, updated_data)


@router.delete("/{plan_id}", response_model=CommonMessageResponse, status_code=status.HTTP_200_OK)
async def delete_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await PlanService.delete_plan(db, current_user["user_id"], plan_id)

@router.get("/{plan_id}/destinations", response_model=List[PlanDestinationResponse], status_code=status.HTTP_200_OK)
async def get_plan_destinations(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await PlanService.get_plan_destinations(db, plan_id, current_user["user_id"])

@router.post("/{plan_id}/destinations", response_model=PlanDestinationResponse, status_code=status.HTTP_201_CREATED)
async def add_destination_to_plan(
    plan_id: int,
    data: PlanDestinationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await PlanService.add_destination_to_plan(db, current_user["user_id"], plan_id, data)

@router.put("/destinations/{plan_destination_id}", response_model=PlanDestinationResponse, status_code=status.HTTP_200_OK)
async def update_plan_destination(
    plan_destination_id: int,
    updated_data: PlanDestinationUpdate,
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await PlanService.update_plan_destination(
        db, 
        current_user["user_id"], 
        plan_id, 
        plan_destination_id, 
        updated_data
        )

@router.delete("/destinations/{plan_destination_id}", response_model=CommonMessageResponse, status_code=status.HTTP_200_OK)
async def remove_destination_from_plan(
    plan_destination_id: int,
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await PlanService.remove_destination_from_plan(db, current_user["user_id"], plan_id, plan_destination_id)

@router.get("/{plan_id}/members", response_model=PlanMemberResponse, status_code=status.HTTP_200_OK)
async def get_plan_members(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await PlanService.get_plan_members(db, plan_id)


@router.post(
    "/{plan_id}/members",
    response_model=PlanMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_members_to_plan(
    plan_id: int,
    data: MemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await PlanService.add_plan_member(db, current_user["user_id"], plan_id, data)


@router.delete(
    "/{plan_id}/members",
    response_model=CommonMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def remove_members_from_plan(
    plan_id: int,
    data: MemberDelete,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await PlanService.remove_plan_member(db, current_user["user_id"], plan_id, data)
