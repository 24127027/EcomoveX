from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from repository.friend_repository import FriendRepository
from repository.user_repository import UserRepository
from schemas.friend_schema import FriendRequest

class FriendService:
    
    @staticmethod
    async def send_friend_request(db: AsyncSession, user_id: int, friend_request: FriendRequest):
        try:
            if user_id == friend_request.friend_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot send friend request to yourself"
                )
            
            friend_user = await UserRepository.get_user_by_id(db, friend_request.friend_id)
            if not friend_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {friend_request.friend_id} not found"
                )
            
            existing = await FriendRepository.get_friendship(db, user_id, friend_request.friend_id)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Friendship already exists"
                )
            
            friendship = await FriendRepository.send_friend_request(db, user_id, friend_request.friend_id)
            if not friendship:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send friend request"
                )
            
            return friendship
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error sending friend request: {e}"
            )
    
    @staticmethod
    async def accept_friend_request(db: AsyncSession, user_id: int, friend_id: int):
        try:
            friendship = await FriendRepository.accept_friend_request(db, user_id, friend_id)
            if not friendship:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Friend request not found"
                )
            return friendship
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
    async def block_user(db: AsyncSession, user_id: int, friend_id: int):
        try:
            if user_id == friend_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot block yourself"
                )
            
            friendship = await FriendRepository.block_user(db, user_id, friend_id)
            if not friendship:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to block user"
                )
            return friendship
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error blocking user: {e}"
            )
    
    @staticmethod
    async def unblock_user(db: AsyncSession, user_id: int, friend_id: int):
        try:
            result = await FriendRepository.unblock_user(db, user_id, friend_id)
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Block not found"
                )
            return {"message": "User unblocked successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error unblocking user: {e}"
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
    async def get_friends(db: AsyncSession, user_id: int):
        try:
            friends = await FriendRepository.get_friends(db, user_id)
            friend_list = []
            
            for friendship in friends:
                friend_user_id = friendship.friend_id if friendship.user_id == user_id else friendship.user_id
                friend_user = await UserRepository.get_user_by_id(db, friend_user_id)
                
                if friend_user:
                    friend_list.append({
                        "user_id": friendship.user_id,
                        "friend_id": friendship.friend_id,
                        "status": friendship.status,
                        "created_at": friendship.created_at,
                        "friend_username": friend_user.username,
                        "friend_email": friend_user.email
                    })
            
            return friend_list
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting friends: {e}"
            )
    
    @staticmethod
    async def get_pending_requests(db: AsyncSession, user_id: int):
        try:
            requests = await FriendRepository.get_pending_requests(db, user_id)
            request_list = []
            
            for request in requests:
                requester = await UserRepository.get_user_by_id(db, request.user_id)
                
                if requester:
                    request_list.append({
                        "user_id": request.user_id,
                        "friend_id": request.friend_id,
                        "status": request.status,
                        "created_at": request.created_at,
                        "friend_username": requester.username,
                        "friend_email": requester.email
                    })
            
            return request_list
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting pending requests: {e}"
            )
    
    @staticmethod
    async def get_sent_requests(db: AsyncSession, user_id: int):
        try:
            requests = await FriendRepository.get_sent_requests(db, user_id)
            request_list = []
            
            for request in requests:
                recipient = await UserRepository.get_user_by_id(db, request.friend_id)
                
                if recipient:
                    request_list.append({
                        "user_id": request.user_id,
                        "friend_id": request.friend_id,
                        "status": request.status,
                        "created_at": request.created_at,
                        "friend_username": recipient.username,
                        "friend_email": recipient.email
                    })
            
            return request_list
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting sent requests: {e}"
            )
    
    @staticmethod
    async def get_blocked_users(db: AsyncSession, user_id: int):
        try:
            blocked = await FriendRepository.get_blocked_users(db, user_id)
            blocked_list = []
            
            for block in blocked:
                blocked_user = await UserRepository.get_user_by_id(db, block.friend_id)
                
                if blocked_user:
                    blocked_list.append({
                        "user_id": block.user_id,
                        "friend_id": block.friend_id,
                        "status": block.status,
                        "created_at": block.created_at,
                        "friend_username": blocked_user.username,
                        "friend_email": blocked_user.email
                    })
            
            return blocked_list
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting blocked users: {e}"
            )
