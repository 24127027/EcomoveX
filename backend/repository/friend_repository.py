from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_
from sqlalchemy.exc import SQLAlchemyError
from models.friend import *

class FriendRepository:
    
    @staticmethod
    async def send_friend_request(db: AsyncSession, user_id: int, friend_id: int):
        try:
            existing = await FriendRepository.get_friendship(db, user_id, friend_id)
            if existing:
                return None
            
            friendship_user = Friend(
                user_id=user_id,
                friend_id=friend_id,
                status=FriendStatus.requested
            )
            db.add(friendship_user)
            await db.commit()
            await db.refresh(friendship_user)
            
            friendship_friend = Friend(
                user_id=friend_id,
                friend_id=user_id,
                status=FriendStatus.pending
            )
            db.add(friendship_friend)
            await db.commit()
            await db.refresh(friendship_friend)
            return friendship_user
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: sending friend request - {e}")
            return None
    
    @staticmethod
    async def accept_friend_request(db: AsyncSession, user_id: int, friend_id: int):
        try:
            # Find the pending request for the current user (who is accepting)
            result_user = await db.execute(
                select(Friend).where(
                    and_(
                        Friend.user_id == user_id,
                        Friend.friend_id == friend_id,
                        Friend.status == FriendStatus.pending
                    )
                )
            )
            friendship_user = result_user.scalar_one_or_none()

            if not friendship_user:
                return None

            friendship_user.status = FriendStatus.friend
            await db.commit()
            await db.refresh(friendship_user)
            
            # Find the requested status for the friend (who sent the request)
            result_friend = await db.execute(
                select(Friend).where(
                    and_(
                        Friend.user_id == friend_id,
                        Friend.friend_id == user_id,
                        Friend.status == FriendStatus.requested
                    )
                )
            )
            friendship_friend = result_friend.scalar_one_or_none()

            if not friendship_friend:
                return None

            friendship_friend.status = FriendStatus.friend
            await db.commit()
            await db.refresh(friendship_friend)

            return friendship_user
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: accepting friend request - {e}")
            return None
    
    @staticmethod
    async def reject_friend_request(db: AsyncSession, user_id: int, friend_id: int):
        try:
            # Find the pending request for the current user (who is rejecting)
            result_user = await db.execute(
                select(Friend).where(
                    and_(
                        Friend.user_id == user_id,
                        Friend.friend_id == friend_id,
                        Friend.status == FriendStatus.pending
                    )
                )
            )
            friendship_user = result_user.scalar_one_or_none()

            if not friendship_user:
                return False

            await db.delete(friendship_user)
            await db.commit()
            
            # Find the requested status for the friend (who sent the request)
            result_friend = await db.execute(
                select(Friend).where(
                    and_(
                        Friend.user_id == friend_id,
                        Friend.friend_id == user_id,
                        Friend.status == FriendStatus.requested
                    )
                )
            )
            friendship_friend = result_friend.scalar_one_or_none()

            if not friendship_friend:
                return False

            await db.delete(friendship_friend)
            await db.commit()
            
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: rejecting friend request - {e}")
            return False
        
    @staticmethod
    async def unfriend(db: AsyncSession, user_id: int, friend_id: int):
        try:
            result = await db.execute(
                select(Friend).where(
                    or_(
                        and_(Friend.user_id == user_id, Friend.friend_id == friend_id),
                        and_(Friend.user_id == friend_id, Friend.friend_id == user_id)
                    )
                )
            )
            friendships = result.scalars().all()
            
            for friendship in friendships:
                await db.delete(friendship)
            
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: unfriending - {e}")
            return False
    
    @staticmethod
    async def get_friendship(db: AsyncSession, user_id: int, friend_id: int):
        try:
            result = await db.execute(
                select(Friend).where(
                    and_(Friend.user_id == user_id, Friend.friend_id == friend_id),
                )
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"ERROR: getting friendship - {e}")
            return None
    
    @staticmethod
    async def get_friends(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(
                select(Friend).where(
                    and_(Friend.user_id == user_id, Friend.status == FriendStatus.friend),
                )
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: getting friends - {e}")
            return []
    
    @staticmethod
    async def get_pending_requests(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(
                select(Friend).where(
                    and_(
                        Friend.friend_id == user_id,
                        Friend.status == FriendStatus.pending
                    )
                )
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: getting pending requests - {e}")
            return []
    
    @staticmethod
    async def get_sent_requests(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(
                select(Friend).where(
                    and_(
                        Friend.user_id == user_id,
                        Friend.status == FriendStatus.requested
                    )
                )
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: getting sent requests - {e}")
            return []
