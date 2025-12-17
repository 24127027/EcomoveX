from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from schemas.message_schema import CommonMessageResponse
from schemas.plan_schema import (
    AllPlansResponse,
    MemberCreate,
    MemberDelete,
    PlanCreate,
    PlanMemberCreate,
    PlanMemberResponse,
    PlanResponse,
    PlanUpdate,
)
from schemas.route_schema import RouteResponse, TransportMode
from services.plan_service import PlanService
from utils.token.authentication_util import get_current_user

router = APIRouter(prefix="/plans", tags=["Plans"])


@router.get("/{plan_id}", response_model=PlanResponse, status_code=status.HTTP_200_OK)
async def get_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    return await PlanService.get_plan_by_id(db, current_user["user_id"], plan_id)


@router.get("/", response_model=AllPlansResponse, status_code=status.HTTP_200_OK)
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
    return await PlanService.update_plan(
        db, current_user["user_id"], plan_id, updated_data
    )


@router.delete(
    "/{plan_id}", response_model=CommonMessageResponse, status_code=status.HTTP_200_OK
)
async def delete_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await PlanService.delete_plan(db, current_user["user_id"], plan_id)


@router.get(
    "/{plan_id}/members",
    response_model=PlanMemberResponse,
    status_code=status.HTTP_200_OK,
)
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
    return await PlanService.remove_plan_member(
        db, current_user["user_id"], plan_id, data
    )


@router.post(
    "/{plan_id}/members/join",
    response_model=CommonMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def join_plan(
    user_id: int,
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await PlanService.add_plan_member(
        db, user_id, plan_id, MemberCreate(PlanMemberCreate(current_user["user_id"]))
    )


@router.get(
    "/{plan_id}/routes",
    response_model=List[RouteResponse],
    status_code=status.HTTP_200_OK,
)
async def get_all_routes(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await PlanService.get_all_routes_by_plan_id(
        db, current_user["user_id"], plan_id
    )


@router.get(
    "/{plan_id}/routes/{origin_plan_destination_id}-{destination_plan_destination_id}",
    response_model=RouteResponse,
    status_code=status.HTTP_200_OK,
)
async def get_route(
    plan_id: int,
    origin_plan_destination_id: int,
    destination_plan_destination_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await PlanService.get_route_by_origin_and_destination(
        db,
        current_user["user_id"],
        plan_id,
        origin_plan_destination_id,
        destination_plan_destination_id,
    )


@router.post(
    "/{plan_id}/routes/{route_id}",
    response_model=RouteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def update_route(
    route_id: int,
    mode: TransportMode,
    carbon_emission_kg: float,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await PlanService.update_route(
        db,
        current_user["user_id"],
        route_id,
        mode,
        carbon_emission_kg,
    )
