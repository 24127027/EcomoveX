from sqlalchemy import and_, delete, or_, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from models.friend import Friend, FriendStatus
from models.user import User


class FriendRepository:
    @staticmethod
    async def send_friend_request(db: AsyncSession, user_id: int, friend_id: int):
        try:
            if user_id == friend_id:
                print("ERROR: Cannot send friend request to yourself")
                return None

            existing = await FriendRepository.get_friendship(db, user_id, friend_id)
            if existing:
                print(
                    f"WARNING: Friendship already exists between {user_id} and {friend_id}"
                )
                return None

            friendship_user = Friend(
                user1_id=min(user_id, friend_id),
                user2_id=max(user_id, friend_id),
                status=FriendStatus.pending,
                action_by=user_id,
            )
            db.add(friendship_user)
            await db.commit()
            await db.refresh(friendship_user)
            return friendship_user
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Failed to send friend request - {type(e).__name__}: {e}")
            return None

    @staticmethod
    async def accept_friend_request(db: AsyncSession, user_id: int, friend_id: int):
        try:
            user1_id = min(user_id, friend_id)
            user2_id = max(user_id, friend_id)

            stmt = (
                update(Friend)
                .where(
                    and_(
                        Friend.user1_id == user1_id,
                        Friend.user2_id == user2_id,
                        Friend.status == FriendStatus.pending,
                        Friend.action_by == friend_id,
                    )
                )
                .values(status=FriendStatus.friend, action_by=user_id)
                .returning(Friend)
            )
            result = await db.execute(stmt)
            await db.commit()

            friendship = result.scalar_one_or_none()
            if friendship:
                await db.refresh(friendship)
            return friendship
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: accepting friend request - {e}")
            return None

    @staticmethod
    async def reject_friend_request(db: AsyncSession, user_id: int, friend_id: int):
        try:
            user1_id = min(user_id, friend_id)
            user2_id = max(user_id, friend_id)

            stmt = delete(Friend).where(
                and_(
                    Friend.user1_id == user1_id,
                    Friend.user2_id == user2_id,
                    Friend.status == FriendStatus.pending,
                    Friend.action_by == friend_id,
                )
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: rejecting friend request - {e}")
            return False

    @staticmethod
    async def cancel_friend_request(db: AsyncSession, user_id: int, friend_id: int):
        try:
            user1_id = min(user_id, friend_id)
            user2_id = max(user_id, friend_id)

            stmt = delete(Friend).where(
                and_(
                    Friend.user1_id == user1_id,
                    Friend.user2_id == user2_id,
                    Friend.status == FriendStatus.pending,
                    Friend.action_by == user_id,
                )
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: canceling friend request - {e}")
            return False

    @staticmethod
    async def unfriend(db: AsyncSession, user_id: int, friend_id: int):
        try:
            user1_id = min(user_id, friend_id)
            user2_id = max(user_id, friend_id)

            stmt = delete(Friend).where(
                and_(
                    Friend.user1_id == user1_id,
                    Friend.user2_id == user2_id,
                    Friend.status == FriendStatus.friend,
                )
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: unfriending - {e}")
            return False

    @staticmethod
    async def get_friendship(db: AsyncSession, user_id: int, friend_id: int):
        try:
            user1_id = min(user_id, friend_id)
            user2_id = max(user_id, friend_id)
            result = await db.execute(
                select(Friend).where(
                    and_(Friend.user1_id == user1_id, Friend.user2_id == user2_id),
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
                    or_(
                        and_(
                            Friend.user1_id == user_id,
                            Friend.status == FriendStatus.friend,
                        ),
                        and_(
                            Friend.user2_id == user_id,
                            Friend.status == FriendStatus.friend,
                        ),
                    )
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
                    or_(
                        and_(
                            Friend.user1_id == user_id,
                            Friend.status == FriendStatus.pending,
                            Friend.action_by != user_id,
                        ),
                        and_(
                            Friend.user2_id == user_id,
                            Friend.status == FriendStatus.pending,
                            Friend.action_by != user_id,
                        ),
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
                    or_(
                        and_(
                            Friend.user1_id == user_id,
                            Friend.status == FriendStatus.pending,
                            Friend.action_by == user_id,
                        ),
                        and_(
                            Friend.user2_id == user_id,
                            Friend.status == FriendStatus.pending,
                            Friend.action_by == user_id,
                        ),
                    )
                )
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: getting sent requests - {e}")
            return []

    @staticmethod
    async def search_friends(
        db: AsyncSession, user_id: int, search_term: str, skip: int = 0, limit: int = 50
    ):
        try:
            query = (
                select(Friend)
                .join(
                    User,
                    or_(
                        and_(Friend.user1_id == User.id, Friend.user2_id == user_id),
                        and_(Friend.user2_id == User.id, Friend.user1_id == user_id),
                    ),
                )
                .where(
                    and_(
                        Friend.status == FriendStatus.friend,
                        or_(Friend.user1_id == user_id, Friend.user2_id == user_id),
                        or_(
                            User.username.ilike(f"%{search_term}%"),
                            User.email.ilike(f"%{search_term}%"),
                        ),
                    )
                )
                .options(selectinload(Friend.user1), selectinload(Friend.user2))
                .offset(skip)
                .limit(limit)
            )
            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: searching friends - {e}")
            return []
