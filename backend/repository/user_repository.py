from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User, UserStatus, Rank
from schema.user_schema import UserCreate, UserUpdate

class UserRepository:        
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            print(f"Error retrieving user by ID {user_id}: {e}")
            return None
        
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str):
        try:
            result = await db.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            print(f"Error retrieving user by email {email}: {e}")
            return None
        
    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str):
        try:
            result = await db.execute(select(User).where(User.username == username))
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            print(f"Error retrieving user by username {username}: {e}")
            return None

    @staticmethod
    async def create_user(db: AsyncSession, user: UserCreate):
        try:
            new_user = User(
                username=user.username,
                email=user.email,
                password=user.password,
                status=UserStatus.active.value,
                eco_points=0,
                rank=Rank.bronze.value
            )
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            return new_user
        except Exception as e:
            await db.rollback()
            print(f"Error creating user: {e}")
            return None

    @staticmethod
    async def update_user(db: AsyncSession, user_id: int, updated_data: UserUpdate):
        try:
            user = await UserRepository.get_user_by_id(db, user_id)
            if not user:
                print(f"User with ID {user_id} not found")
                return None

            if updated_data.old_password != user.password:
                print("Old password does not match")
                return None

            for var, value in updated_data.dict(exclude_unset=True).items():
                setattr(user, var, value)

            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except Exception as e:
            await db.rollback()
            print(f"Error updating user ID {user_id}: {e}")
            return None
        
    @staticmethod
    async def update_user_status(db: AsyncSession, user_id: int, status: UserStatus):
        try:
            user = await UserRepository.get_user_by_id(db, user_id)
            if not user:
                print(f"User with ID {user_id} not found")
                return None

            user.status = status.value
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except Exception as e:
            await db.rollback()
            print(f"Error updating status for user ID {user_id}: {e}")
            return None
        
    @staticmethod
    async def update_eco_points(db: AsyncSession, user_id: int, points: int):
        try:
            user = await UserRepository.get_user_by_id(db, user_id)
            if not user:
                print(f"User with ID {user_id} not found")
                return None

            user.eco_points = points
            await UserRepository.update_rank(db, user_id)
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except Exception as e:
            await db.rollback()
            print(f"Error updating eco points for user ID {user_id}: {e}")
            return None
        
    @staticmethod
    async def update_rank(db: AsyncSession, user_id: int):
        try:
            user = await UserRepository.get_user_by_id(db, user_id)
            if not user:
                print(f"User with ID {user_id} not found")
                return None

            if user.eco_points <= 500:
                user.rank = Rank.bronze.value
            elif user.eco_points <= 2000:
                user.rank = Rank.silver.value
            elif user.eco_points <= 5000:
                user.rank = Rank.gold.value
            elif user.eco_points <= 10000:
                user.rank = Rank.platinum.value
            else:
                user.rank = Rank.diamond.value

            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except Exception as e:
            await db.rollback()
            print(f"Error updating rank for user ID {user_id}: {e}")
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
        except Exception as e:
            await db.rollback()
            print(f"Error deleting user ID {user_id}: {e}")
            return False
        
    @staticmethod
    async def is_user_online(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user or not user.last_seen:
                return False
            return datetime.utcnow() - user.last_seen <= timedelta(minutes=2)
        except Exception as e:
            await db.rollback()
            print(f"Error checking online status for user ID {user_id}: {e}")
            return False