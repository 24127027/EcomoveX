from typing import List
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User
from utils.config import settings

class UserRepository:
    @staticmethod
    async def update_password_by_user(db: AsyncSession, user_id: int, current_password: str, new_password: str) -> bool:
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                return False

            if not pwd_context.verify(current_password, user.password):
                return False

            user.password = pwd_context.hash(new_password)
            db.add(user)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Failed to change password for user {user_id} - {e}")
            return False
            
    async def get_user_by_email(db: AsyncSession, email: str):
        try:
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if not user:
                raise ValueError(f"Email {email} is not registered!")
            return user
        except Exception as e:
            raise RuntimeError(f"Database error: {e}")

    @staticmethod
    async def admin_update_password(db: AsyncSession, user_id: int, new_password: str) -> bool:
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                return False
            user.password = new_password
            db.add(user)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Failed to update password for user {user_id} - {e}")
            return False


