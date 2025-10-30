from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from models.user import User, Rank
from schema.user_schema import UserProfileUpdate, UserCredentialUpdate
from schema.authentication_schema import UserRegister

class UserRepository:
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error retrieving user by ID {user_id}: {e}")
            return None
                  
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str):
        try:
            result = await db.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error retrieving user by email {email}: {e}")
            return None
        
    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str):
        try:
            result = await db.execute(select(User).where(User.username == username))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error retrieving user by username {username}: {e}")
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
            print(f"Error creating user: {e}")
            return None

    @staticmethod
    async def update_user_profile(db: AsyncSession, user_id: int, updated_data: UserProfileUpdate):
        try:
            user = await UserRepository.get_user_by_id(db, user_id)
            if not user:
                print(f"User with ID {user_id} not found")
                return None

            # Password verification is done in service layer
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
            print(f"Error updating user ID {user_id}: {e}")
            return None
        
    @staticmethod
    async def update_user_credential(db: AsyncSession, user_id: int, updated_data: UserCredentialUpdate):
        try:
            user = await UserRepository.get_user_by_id(db, user_id)
            if not user:
                print(f"User with ID {user_id} not found")
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
            print(f"Error updating user information {user_id}: {e}")
            return None
        
    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int):
        try:
            user = await UserRepository.get_user_by_id(db, user_id)
            if not user:
                print(f"User with ID {user_id} not found")
                return False

            await db.delete(user)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error deleting user ID {user_id}: {e}")
            return False