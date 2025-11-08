from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_
from sqlalchemy.exc import SQLAlchemyError
from models.friend import Friend, FriendStatus

class FriendRepository:
    
    @staticmethod
    async def send_friend_request(db: AsyncSession, user_id: int, friend_id: int):
        try:
            existing = await FriendRepository.get_friendship(db, user_id, friend_id)
            if existing:
                return None
            
            friendship = Friend(
                user_id=user_id,
                friend_id=friend_id,
                status=FriendStatus.pending
            )
            db.add(friendship)
            await db.commit()
            await db.refresh(friendship)
            return friendship
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error sending friend request: {e}")
            return None
    
    @staticmethod
    async def accept_friend_request(db: AsyncSession, user_id: int, friend_id: int):
        try:
            result = await db.execute(
                select(Friend).where(
                    and_(
                        Friend.user_id == friend_id,
                        Friend.friend_id == user_id,
                        Friend.status == FriendStatus.pending
                    )
                )
            )
            friendship = result.scalar_one_or_none()
            
            if not friendship:
                return None
            
            friendship.status = FriendStatus.accepted
            await db.commit()
            await db.refresh(friendship)
            return friendship
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error accepting friend request: {e}")
            return None
    
    @staticmethod
    async def reject_friend_request(db: AsyncSession, user_id: int, friend_id: int):
        try:
            result = await db.execute(
                select(Friend).where(
                    and_(
                        Friend.user_id == friend_id,
                        Friend.friend_id == user_id,
                        Friend.status == FriendStatus.pending
                    )
                )
            )
            friendship = result.scalar_one_or_none()
            
            if not friendship:
                return False
            
            await db.delete(friendship)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error rejecting friend request: {e}")
            return False
    
    @staticmethod
    async def block_user(db: AsyncSession, user_id: int, friend_id: int):
        try:
            friendship = await FriendRepository.get_friendship(db, user_id, friend_id)
            
            if friendship:
                friendship.status = FriendStatus.blocked
            else:
                friendship = Friend(
                    user_id=user_id,
                    friend_id=friend_id,
                    status=FriendStatus.blocked
                )
                db.add(friendship)
            
            await db.commit()
            await db.refresh(friendship)
            return friendship
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error blocking user: {e}")
            return None
    
    @staticmethod
    async def unblock_user(db: AsyncSession, user_id: int, friend_id: int):
        try:
            result = await db.execute(
                select(Friend).where(
                    and_(
                        Friend.user_id == user_id,
                        Friend.friend_id == friend_id,
                        Friend.status == FriendStatus.blocked
                    )
                )
            )
            friendship = result.scalar_one_or_none()
            
            if not friendship:
                return False
            
            await db.delete(friendship)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error unblocking user: {e}")
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
            print(f"Error unfriending: {e}")
            return False
    
    @staticmethod
    async def get_friendship(db: AsyncSession, user_id: int, friend_id: int):
        try:
            result = await db.execute(
                select(Friend).where(
                    or_(
                        and_(Friend.user_id == user_id, Friend.friend_id == friend_id),
                        and_(Friend.user_id == friend_id, Friend.friend_id == user_id)
                    )
                )
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"Error getting friendship: {e}")
            return None
    
    @staticmethod
    async def get_friends(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(
                select(Friend).where(
                    or_(
                        and_(Friend.user_id == user_id, Friend.status == FriendStatus.accepted),
                        and_(Friend.friend_id == user_id, Friend.status == FriendStatus.accepted)
                    )
                )
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"Error getting friends: {e}")
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
            print(f"Error getting pending requests: {e}")
            return []
    
    @staticmethod
    async def get_sent_requests(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(
                select(Friend).where(
                    and_(
                        Friend.user_id == user_id,
                        Friend.status == FriendStatus.pending
                    )
                )
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"Error getting sent requests: {e}")
            return []
    
    @staticmethod
    async def get_blocked_users(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(
                select(Friend).where(
                    and_(
                        Friend.user_id == user_id,
                        Friend.status == FriendStatus.blocked
                    )
                )
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"Error getting blocked users: {e}")
            return []
    
    @staticmethod
    async def are_friends(db: AsyncSession, user_id: int, friend_id: int) -> bool:
        try:
            result = await db.execute(
                select(Friend).where(
                    or_(
                        and_(Friend.user_id == user_id, Friend.friend_id == friend_id, Friend.status == FriendStatus.accepted),
                        and_(Friend.user_id == friend_id, Friend.friend_id == user_id, Friend.status == FriendStatus.accepted)
                    )
                )
            )
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            print(f"Error checking friendship: {e}")
            return False
    
    @staticmethod
    async def is_blocked(db: AsyncSession, user_id: int, friend_id: int) -> bool:
        try:
            result = await db.execute(
                select(Friend).where(
                    and_(
                        Friend.user_id == user_id,
                        Friend.friend_id == friend_id,
                        Friend.status == FriendStatus.blocked
                    )
                )
            )
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            print(f"Error checking block status: {e}")
            return False