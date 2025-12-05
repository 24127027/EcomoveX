from typing import List

from fastapi import APIRouter, Body, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from schemas.friend_schema import FriendRequestByUsername, FriendResponse
from schemas.message_schema import CommonMessageResponse
from services.friend_service import FriendService
from utils.token.authentication_util import get_current_user

router = APIRouter(prefix="/friends", tags=["friends"])


@router.post(
    "/request/by-username",
    response_model=FriendResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_friend_request_by_username(
    request_data: FriendRequestByUsername = Body(...),
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Gửi lời mời kết bạn bằng username.
    
    - **username**: Username của người muốn kết bạn (case-insensitive)
    
    Returns:
    - 201: Gửi lời mời thành công
    - 404: Không tìm thấy user với username này
    - 400: Không thể kết bạn với chính mình hoặc đã là bạn
    """
    return await FriendService.send_friend_request_by_username(
        user_db, current_user["user_id"], request_data.username
    )


@router.post(
    "/{friend_id}/request",
    response_model=FriendResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_friend_request(
    friend_id: int = Path(...),
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await FriendService.send_friend_request(
        user_db, current_user["user_id"], friend_id
    )


@router.post(
    "/{friend_id}/accept", response_model=FriendResponse, status_code=status.HTTP_200_OK
)
async def accept_friend_request(
    friend_id: int = Path(...),
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await FriendService.accept_friend_request(
        user_db, current_user["user_id"], friend_id
    )


@router.delete(
    "/{friend_id}/reject",
    response_model=CommonMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def reject_friend_request(
    friend_id: int = Path(...),
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await FriendService.reject_friend_request(
        user_db, current_user["user_id"], friend_id
    )


@router.delete(
    "/{friend_id}",
    response_model=CommonMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def unfriend(
    friend_id: int = Path(...),
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await FriendService.unfriend(user_db, current_user["user_id"], friend_id)


@router.get("/", response_model=List[FriendResponse], status_code=status.HTTP_200_OK)
async def get_friends(
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await FriendService.get_friends(user_db, current_user["user_id"])


@router.get(
    "/pending", response_model=List[FriendResponse], status_code=status.HTTP_200_OK
)
async def get_pending_requests(
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await FriendService.get_pending_requests(user_db, current_user["user_id"])


@router.get(
    "/sent", response_model=List[FriendResponse], status_code=status.HTTP_200_OK
)
async def get_sent_requests(
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await FriendService.get_sent_requests(user_db, current_user["user_id"])
