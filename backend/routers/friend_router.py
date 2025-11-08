from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from schemas.friend_schema import FriendRequest, FriendResponse, FriendWithUserInfo
from services.friend_service import FriendService
from database.user_database import get_user_db
from utils.authentication_util import get_current_user

router = APIRouter(prefix="/friends", tags=["friends"])

@router.post("/request", response_model=FriendResponse, status_code=status.HTTP_201_CREATED)
async def send_friend_request(
    friend_request: FriendRequest,
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await FriendService.send_friend_request(db, current_user["user_id"], friend_request)

@router.post("/{friend_id}/accept", response_model=FriendResponse, status_code=status.HTTP_200_OK)
async def accept_friend_request(
    friend_id: int,
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await FriendService.accept_friend_request(db, current_user["user_id"], friend_id)

@router.delete("/{friend_id}/reject", status_code=status.HTTP_200_OK)
async def reject_friend_request(
    friend_id: int,
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await FriendService.reject_friend_request(db, current_user["user_id"], friend_id)

@router.post("/{friend_id}/block", response_model=FriendResponse, status_code=status.HTTP_200_OK)
async def block_user(
    friend_id: int,
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await FriendService.block_user(db, current_user["user_id"], friend_id)

@router.delete("/{friend_id}/unblock", status_code=status.HTTP_200_OK)
async def unblock_user(
    friend_id: int,
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await FriendService.unblock_user(db, current_user["user_id"], friend_id)

@router.delete("/{friend_id}", status_code=status.HTTP_200_OK)
async def unfriend(
    friend_id: int,
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await FriendService.unfriend(db, current_user["user_id"], friend_id)

@router.get("/", response_model=List[FriendWithUserInfo], status_code=status.HTTP_200_OK)
async def get_friends(
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await FriendService.get_friends(db, current_user["user_id"])

@router.get("/pending", response_model=List[FriendWithUserInfo], status_code=status.HTTP_200_OK)
async def get_pending_requests(
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await FriendService.get_pending_requests(db, current_user["user_id"])

@router.get("/sent", response_model=List[FriendWithUserInfo], status_code=status.HTTP_200_OK)
async def get_sent_requests(
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await FriendService.get_sent_requests(db, current_user["user_id"])

@router.get("/blocked", response_model=List[FriendWithUserInfo], status_code=status.HTTP_200_OK)
async def get_blocked_users(
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await FriendService.get_blocked_users(db, current_user["user_id"])