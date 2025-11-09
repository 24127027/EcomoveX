from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import *
from schemas.authentication_schema import *
from schemas.user_schema import *

class UserRepository:
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
    async def get_user_by_email(db: AsyncSession, email: str):
        try:
            result = await db.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Failed to retrieve user by email {email} - {e}")
            return None
        
    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str):
        try:
            result = await db.execute(select(User).where(User.username == username))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Failed to retrieve user by username {username} - {e}")
            return None

    @staticmethod
    async def create_user(db: AsyncSession, user: UserRegister):
        try:
            new_user = User(
                username=user.username,
                email=user.email,
                password=user.password,
                eco_point=0,
                rank=Rank.bronze.value
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
    async def update_user_credentials(db: AsyncSession, user_id: int, updated_data: UserCredentialUpdate):
        try:
            user = await UserRepository.get_user_by_id(db, user_id)
            if not user:
                print(f"WARNING: WARNING: User not found with ID {user_id}")
                return None

            if updated_data.new_username is not None:
                user.username = updated_data.new_username
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
    async def update_user_profile(db: AsyncSession, user_id: int, updated_data: UserProfileUpdate):
        try:
            user = await UserRepository.get_user_by_id(db, user_id)
            if not user:
                print(f"WARNING: WARNING: User not found with ID {user_id}")
                return None

            if updated_data.eco_point is not None:
                user.eco_point = updated_data.eco_point
            if updated_data.rank is not None:
                user.rank = updated_data.rank

            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Failed to update user profile for ID {user_id} - {e}")
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
        
class UserActivityRepository:
    @staticmethod
    async def log_user_activity(db: AsyncSession, user_id: int, data: UserActivityCreate):
        try:
            new_activity = UserActivity(
                user_id=user_id,
                activity_type=data.activity_type,
                destination_id=data.destination_id,
                timestamp=func.now()
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
