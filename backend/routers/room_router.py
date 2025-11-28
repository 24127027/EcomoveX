from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db
from schemas.room_schema import *
from services.room_service import RoomService
from utils.token.authentication_util import get_current_user

router = APIRouter(prefix="/rooms", tags=["Rooms"])

@router.get("/rooms", response_model=list[RoomResponse], status_code=status.HTTP_200_OK)
async def list_rooms(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await RoomService.get_all_rooms_for_user(db, current_user["user_id"])

@router.get("/direct-rooms", response_model=list[RoomDirectResponse], status_code=status.HTTP_200_OK)
async def list_direct_rooms(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await RoomService.get_all_direct_rooms_for_user(db, current_user["user_id"])

@router.get("/rooms/{room_id}", response_model=RoomResponse, status_code=status.HTTP_200_OK)
async def get_room(
    room_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await RoomService.get_room(db, current_user["user_id"], room_id)

@router.get("/direct-rooms/{direct_room_id}", response_model=RoomDirectResponse, status_code=status.HTTP_200_OK)
async def get_direct_room(
    direct_room_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await RoomService.get_direct_room(db, current_user["user_id"], direct_room_id)

@router.post("/rooms", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: RoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await RoomService.create_room(
        db, 
        current_user["user_id"], 
        room_data
    )

@router.post("/rooms/{room_id}/members", response_model=RoomResponse, status_code=status.HTTP_200_OK)
async def add_users_to_room(
    room_id: int = Path(..., gt=0),
    member_data: AddMemberRequest = ...,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await RoomService.add_users_to_room(
        db, 
        current_user["user_id"], 
        room_id,
        member_data
    )

@router.delete("/rooms/{room_id}/members", response_model=RoomResponse, status_code=status.HTTP_200_OK)
async def remove_users_from_room(
    room_id: int = Path(..., gt=0),
    member_data: RemoveMemberRequest = ...,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await RoomService.remove_users_from_room(
        db, 
        current_user["user_id"], 
        member_data.ids, 
        room_id
    )