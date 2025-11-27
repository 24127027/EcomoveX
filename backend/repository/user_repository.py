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
    async def create_user(db: AsyncSession, user_data: UserCreate):
        try:
            existed_email = await UserRepository.get_user_by_email(db, user_data.email)
            if existed_email:
                print(f"WARNING: User with email {user_data.email} already exists")
                return None
            existing_username = await UserRepository.get_user_by_username(db, user_data.username)
            if existing_username:
                print(f"WARNING: Username {user_data.username} already taken")
                return None
            new_user = User(
                username=user_data.username,
                email=user_data.email,
                password=user_data.password,
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
    async def log_user_activity(db: AsyncSession, user_id: int, data: UserActivityCreate):
        try:
            new_activity = UserActivity(
                user_id=user_id,
                activity=data.activity,
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
    
    @staticmethod
    async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 100):
        try:
            result = await db.execute(
                select(User)
                .order_by(User.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: Failed to retrieve all users - {e}")
            return []
    
    @staticmethod
    async def search_users(db: AsyncSession, search_term: str, skip: int = 0, limit: int = 50):
        try:
            result = await db.execute(
                select(User)
                .where(
                    (User.username.ilike(f"%{search_term}%")) |
                    (User.email.ilike(f"%{search_term}%"))
                )
                .order_by(User.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: Failed to search users with term '{search_term}' - {e}")
            return []
