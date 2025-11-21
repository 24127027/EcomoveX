from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from services.room_service import RoomService
from services.user_service import UserService
from repository.friend_repository import FriendRepository
from repository.user_repository import UserRepository
from schemas.friend_schema import *
from schemas.user_schema import *

class FriendService:
    @staticmethod
    async def send_friend_request(db: AsyncSession, user_id: int, friend_id: int) -> FriendResponse:
        try:
            if user_id == friend_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot send friend request to yourself"
                )
            
            friend_user = await UserRepository.get_user_by_id(db, friend_id)
            if not friend_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {friend_id} not found"
                )
            
            existing = await FriendRepository.get_friendship(db, user_id, friend_id)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Friendship already exists"
                )
            
            friendship = await FriendRepository.send_friend_request(db, user_id, friend_id)
            if not friendship:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send friend request"
                )
            return FriendResponse(
                user_id=user_id,
                friend_id=friend_id,
                status=friendship.status,
                created_at=friendship.created_at
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error sending friend request: {e}"
            )
    
    @staticmethod
    async def accept_friend_request(db: AsyncSession, user_id: int, friend_id: int) -> FriendResponse:
        try:
            friendship = await FriendRepository.accept_friend_request(db, user_id, friend_id)
            if not friendship:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Friend request not found"
                )
                
            await RoomService.create_direct_room(db, user_id, friend_id)
                
            return FriendResponse(
                user_id=user_id,
                friend_id=friend_id,
                status=friendship.status,
                created_at=friendship.created_at
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error accepting friend request: {e}"
            )
    
    @staticmethod
    async def reject_friend_request(db: AsyncSession, user_id: int, friend_id: int):
        try:
            result = await FriendRepository.reject_friend_request(db, user_id, friend_id)
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Friend request not found"
                )
            return {"message": "Friend request rejected successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error rejecting friend request: {e}"
            )
        
    @staticmethod
    async def unfriend(db: AsyncSession, user_id: int, friend_id: int):
        try:
            result = await FriendRepository.unfriend(db, user_id, friend_id)
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Friendship not found"
                )
            return {"message": "Unfriended successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error unfriending: {e}"
            )
    
    @staticmethod
    async def get_friends(db: AsyncSession, user_id: int) -> List[FriendResponse]:
        try:
            friends = await FriendRepository.get_friends(db, user_id)
            friend_list = []
            
            for friendship in friends:
                friend_user_id = friendship.user1_id if friendship.user2_id == user_id else friendship.user2_id
                friend_user = await UserRepository.get_user_by_id(db, friend_user_id)
                
                if friend_user:
                    friend_list.append(FriendResponse(
                        user_id=user_id,
                        friend_id=friend_user_id,
                        status=friendship.status,
                        created_at=friendship.created_at
                    ))
            
            return friend_list
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting friends: {e}"
            )
    
    @staticmethod
    async def get_pending_requests(db: AsyncSession, user_id: int) -> List[FriendResponse]:
        try:
            requests = await FriendRepository.get_pending_requests(db, user_id)
            request_list = []
            
            for request in requests:
                request_list.append(FriendResponse(
                    user_id=user_id,
                    friend_id=request.user1_id if request.user2_id == user_id else request.user2_id,
                    status=request.status,
                    created_at=request.created_at
                ))
            
            return request_list
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting pending requests: {e}"
            )
    
    @staticmethod
    async def get_sent_requests(db: AsyncSession, user_id: int) -> List[FriendResponse]:
        try:
            from schemas.friend_schema import FriendResponse
            requests = await FriendRepository.get_sent_requests(db, user_id)
            request_list = []
            
            for request in requests:
                    request_list.append(FriendResponse(
                    user_id=user_id,
                    friend_id=request.user1_id if request.user2_id == user_id else request.user2_id,
                    status=request.status,
                    created_at=request.created_at
                ))
            
            return request_list
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting sent requests: {e}"
            )