from typing import List

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.user import Rank, Role, User, UserActivity
from schemas.user_schema import (
    UserActivityCreate,
    UserCreate,
    UserCredentialUpdate,
    UserFilterParams,
    UserProfileUpdate,
    UserUpdateEcoPoint,
)
from utils.config import settings


class UserRepository:
    @staticmethod
    async def fetch_users(db: AsyncSession, filters: UserFilterParams) -> List[User]:
        """
        Fetch raw User ORM objects from DB with filters & pagination
        """
        try:
            query = (
                select(User)
                .options(
                    selectinload(User.rooms),
                    selectinload(User.reviews),
                    selectinload(User.missions),
                )
                .order_by(User.created_at.desc())
            )

            if filters.search:
                search = f"%{filters.search}%"
                query = query.where(
                    (User.username.ilike(search)) | (User.email.ilike(search))
                )

            if filters.role:
                query = query.where(User.role == filters.role)

            if filters.created_from:
                query = query.where(User.created_at >= filters.created_from)

            if filters.created_to:
                query = query.where(User.created_at <= filters.created_to)

            query = query.offset(filters.skip).limit(filters.limit)

            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: Failed to list users - {e}")
            return []

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Failed to retrieve user by ID {user_id} - {e}")
            return None

    @staticmethod
    async def get_users_by_ids(db: AsyncSession, user_ids: List[int]):
        try:
            result = await db.execute(select(User).where(User.id.in_(user_ids)))
            return result.scalars().all()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Failed to retrieve users by IDs - {e}")
            return []

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str):
        """
        Get a single user by email address.
        """
        try:
            result = await db.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"ERROR: Failed to fetch user by email '{email}' - {e}")
            return None

    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate):
        try:
            is_existing = await UserRepository.search_users(db, user_data.username) or await UserRepository.search_users(db, user_data.email)
            if is_existing:
                print(
                    f"WARNING: WARNING: User creation failed - username "
                    f"'{user_data.username}' already exists"
                )
                return None
            
            # Check if this should be an admin based on FIRST_ADMIN_EMAIL
            user_role = Role.user.value  # Default role (use .value for string)
            if settings.FIRST_ADMIN_EMAIL and user_data.email == settings.FIRST_ADMIN_EMAIL:
                user_role = Role.admin.value
                print(f"INFO: Creating admin user for {user_data.email}")
            
            new_user = User(
                username=user_data.username,
                email=user_data.email,
                password=user_data.password,
                eco_point=0,
                rank=Rank.bronze.value,
                role=user_role,
            )
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            return new_user
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Failed to create user - {e}")
            return None

    @staticmethod
    async def update_user_credentials(
        db: AsyncSession, user_id: int, updated_data: UserCredentialUpdate
    ):
        try:
            user = await UserRepository.get_user_by_id(db, user_id)
            if not user:
                print(f"WARNING: WARNING: User not found with ID {user_id}")
                return None

            if updated_data.new_email is not None:
                user.email = updated_data.new_email
            if updated_data.new_password is not None:
                user.password = updated_data.new_password

            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Failed to update user credentials for ID {user_id} - {e}")
            return None

    @staticmethod
    async def update_user_profile(
        db: AsyncSession, user_id: int, updated_data: UserProfileUpdate
    ):
        try:
            user = await UserRepository.get_user_by_id(db, user_id)
            if not user:
                print(f"WARNING: WARNING: User not found with ID {user_id}")
                return None

            if updated_data.username is not None:
                user.username = updated_data.username
            if updated_data.avt_blob_name is not None:
                user.avt_blob_name = updated_data.avt_blob_name
            if updated_data.cover_blob_name is not None:
                user.cover_blob_name = updated_data.cover_blob_name

            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Failed to update user profile for ID {user_id} - {e}")
            return None

    @staticmethod
    async def add_eco_point(db: AsyncSession, user_id: int, data: UserUpdateEcoPoint):
        try:
            user = await UserRepository.get_user_by_id(db, user_id)
            if not user:
                print(f"WARNING: WARNING: User not found with ID {user_id}")
                return None

            user.eco_point = data.point
            user.rank = data.rank

            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Failed to add eco point for user ID {user_id} - {e}")
            return None

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int):
        try:
            user = await UserRepository.get_user_by_id(db, user_id)
            if not user:
                print(f"WARNING: WARNING: User not found with ID {user_id}")
                return False

            await db.delete(user)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Failed to delete user with ID {user_id} - {e}")
            return False

    @staticmethod
    async def log_user_activity(
        db: AsyncSession, user_id: int, data: UserActivityCreate
    ):
        try:
            new_activity = UserActivity(
                user_id=user_id,
                activity=data.activity,
                destination_id=data.destination_id,
                timestamp=func.now(),
            )
            db.add(new_activity)
            await db.commit()
            await db.refresh(new_activity)
            return new_activity
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Failed to log activity for user ID {user_id} - {e}")
            return None

    @staticmethod
    async def get_user_activities(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(
                select(UserActivity)
                .where(UserActivity.user_id == user_id)
                .order_by(UserActivity.timestamp.desc())
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Failed to retrieve activities for user ID {user_id} - {e}")
            return []

    @staticmethod
    async def search_users(
        db: AsyncSession, search_term: str, skip: int = 0, limit: int = 50
    ):
        try:
            result = await db.execute(
                select(User)
                .options(
                    selectinload(User.rooms),
                    selectinload(User.reviews),
                    selectinload(User.missions),
                )
                .where(
                    (User.username.ilike(f"%{search_term}%"))
                    | (User.email.ilike(f"%{search_term}%"))
                )
                .order_by(User.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: Failed to search users with term '{search_term}' - {e}")
            return []

    @staticmethod
    async def admin_update_password(
        db: AsyncSession, user_id: int, new_password: str
    ) -> bool:
        """
        Admin updates a user's password without requiring the old password.
        """
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                return False

            user.password = new_password
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Failed to update password for user ID {user_id} - {e}")
            return False

    @staticmethod
    async def admin_update_role(db: AsyncSession, user_id: int, new_role) -> User:
        """
        Admin updates a user's role.
        """
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                return None

            user.role = new_role
            await db.commit()
            await db.refresh(user)
            return user
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Failed to update role for user ID {user_id} - {e}")
            return None
