from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from models.user import User
from models.badge import Badge, UserBadge
from schema.badge_schema import BadgeCreate, BadgeUpdate

class BadgeRepository:
    @staticmethod
    async def get_all_badges(db: AsyncSession):
        try:
            result = await db.execute(select(Badge))
            return result.scalars().all()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error fetching all badges: {e}")
            return []

    @staticmethod
    async def get_badge_by_id(db: AsyncSession, badge_id: int):
        try:
            result = await db.execute(select(Badge).where(Badge.id == badge_id))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error fetching badge with id {badge_id}: {e}")
            return None
        
    @staticmethod
    async def get_badge_by_name(db: AsyncSession, name: str):
        try:
            result = await db.execute(select(Badge).where(func.lower(Badge.name) == name.lower()))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error fetching badge with name {name}: {e}")
            return None

    @staticmethod
    async def create_badge(db: AsyncSession, badge_data: BadgeCreate):
        try:
            new_badge = Badge(
                name=badge_data.name,
                description=badge_data.description
            )
            db.add(new_badge)
            await db.commit()
            await db.refresh(new_badge)
            return new_badge
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error creating badge: {badge_data}, {e}")
            return None

    @staticmethod
    async def update_badge(db: AsyncSession, badge_id: int, updated_data: BadgeUpdate):
        try:
            result = await db.execute(select(Badge).where(Badge.id == badge_id))
            badge = result.scalar_one_or_none()
            if not badge:
                print(f"Badge with id {badge_id} not found for update.")
                return None

            if updated_data.name is not None:
                badge.name = updated_data.name
            if updated_data.description is not None:
                badge.description = updated_data.description

            db.add(badge)
            await db.commit()
            await db.refresh(badge)
            return badge
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error updating badge with id {badge_id}: {e}")
            return None

    @staticmethod
    async def delete_badge(db: AsyncSession, badge_id: int):
        try:
            result = await db.execute(select(Badge).where(Badge.id == badge_id))
            badge = result.scalar_one_or_none()
            if not badge:
                return False

            await db.delete(badge)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error deleting badge with id {badge_id}: {e}")
            return False

class UserBadgeRepository:
    @staticmethod
    async def add_badge_to_user(db: AsyncSession, user_id: int, badge_id: int):
        try:
            user = await db.get(User, user_id)
            badge = await db.get(Badge, badge_id)
            if not user or not badge:
                print(f"User or Badge not found (user={user_id}, badge={badge_id})")
                return None

            existing = UserBadgeRepository.has_badge(db, user_id, badge_id)
            if existing:
                print("User already owns this badge.")
                return existing

            new_user_badge = UserBadge(
                user_id=user_id,
                badge_id=badge_id,
                obtained_at=datetime.utcnow(),
            )
            db.add(new_user_badge)

            if hasattr(user, "eco_point") and hasattr(badge, "value"):
                user.eco_point = (user.eco_point or 0) + (badge.value or 0)
                db.add(user)

            await db.commit()
            await db.refresh(new_user_badge)
            return new_user_badge

        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error while adding badge to user: {e}")
            return None

    @staticmethod
    async def get_user_badges(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(
                select(UserBadge).where(UserBadge.user_id == user_id)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error fetching user badges for user {user_id}: {e}")
            return []

    @staticmethod
    async def has_badge(db: AsyncSession, user_id: int, badge_id: int):
        try:
            result = await db.execute(
                select(UserBadge)
                .where(UserBadge.user_id == user_id, UserBadge.badge_id == badge_id)
            )
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            print(f"Error checking if user has badge: {e}")
            return False

    @staticmethod
    async def remove_user_badge(db: AsyncSession, user_id: int, badge_id: int):
        try:
            result = await db.execute(
                select(UserBadge).where(
                    UserBadge.user_id == user_id,
                    UserBadge.badge_id == badge_id
                )
            )
            user_badge = result.scalar_one_or_none()
            if not user_badge:
                print(f"Badge {badge_id} not found for user {user_id}.")
                return False

            await db.delete(user_badge)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error deleting badge for user {user_id}: {e}")
            return False