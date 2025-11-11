from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.user_database import get_user_db
from schemas.friend_schema import *
from services.friend_service import FriendService
from utils.authentication_util import get_current_user

router = APIRouter(prefix="/friends", tags=["friends"])

@router.post("/{friend_id}/request", response_model=FriendResponse, status_code=status.HTTP_201_CREATED)
async def send_friend_request(
    friend_id: int,
    user_db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    friend_request = FriendRequest(friend_id=friend_id)
    return await FriendService.send_friend_request(user_db, current_user["user_id"], friend_request)

@router.post("/{friend_id}/accept", response_model=FriendResponse, status_code=status.HTTP_200_OK)
async def accept_friend_request(
    friend_id: int,
    user_db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await FriendService.accept_friend_request(user_db, current_user["user_id"], friend_id)

@router.delete("/{friend_id}/reject", status_code=status.HTTP_200_OK)
async def reject_friend_request(
    friend_id: int,
    user_db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await FriendService.reject_friend_request(user_db, current_user["user_id"], friend_id)

@router.delete("/{friend_id}", status_code=status.HTTP_200_OK)
async def unfriend(
    friend_id: int,
    user_db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await FriendService.unfriend(user_db, current_user["user_id"], friend_id)

@router.get("/", response_model=List[FriendResponse], status_code=status.HTTP_200_OK)
async def get_friends(
    user_db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await FriendService.get_friends(user_db, current_user["user_id"])

@router.get("/pending", response_model=List[FriendResponse], status_code=status.HTTP_200_OK)
async def get_pending_requests(
    user_db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await FriendService.get_pending_requests(user_db, current_user["user_id"])

@router.get("/sent", response_model=List[FriendResponse], status_code=status.HTTP_200_OK)
async def get_sent_requests(
    user_db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await FriendService.get_sent_requests(user_db, current_user["user_id"])