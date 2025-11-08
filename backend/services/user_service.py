from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from models.user import Rank
from repository.user_repository import UserRepository
from schemas.user_schema import UserProfileUpdate, UserCredentialUpdate, UserActivityCreate
from schemas.authentication_schema import UserRegister

class UserService:
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int):
        try:
            user = await UserRepository.get_user_by_id(db, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found"
                )
            return user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving user by ID {user_id}: {e}"
            )

    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserRegister):
        try:
            existing = await UserRepository.get_user_by_email(db, user_data.email)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )

            user = await UserRepository.create_user(db, user_data)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user"
                )
            return user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error creating user: {e}"
            )

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str):
        try:
            user = await UserRepository.get_user_by_email(db, email)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with email '{email}' not found"
                )
            return user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving user by email {email}: {e}"
            )

    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str):
        try:
            user = await UserRepository.get_user_by_username(db, username)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with username '{username}' not found"
                )
            return user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving user by username {username}: {e}"
            )

    @staticmethod
    async def add_eco_point(db: AsyncSession, user_id: int, point: int):
        try:
            if point <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Points must be greater than zero"
                )

            user = await UserRepository.get_user_by_id(db, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found"
                )

            user_update = UserProfileUpdate()
            user_update.eco_point = (user.eco_point or 0) + point

            if user_update.eco_point <= 500:
                user_update.rank = Rank.bronze
            elif user_update.eco_point <= 2000:
                user_update.rank = Rank.silver
            elif user_update.eco_point <= 5000:
                user_update.rank = Rank.gold
            elif user_update.eco_point <= 10000:
                user_update.rank = Rank.platinum
            else:
                user_update.rank = Rank.diamond

            updated_user = await UserRepository.update_user_profile(db, user_id, user_update)
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to update eco point for user {user_id}"
                )

            return updated_user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error updating eco point for user {user_id}: {e}"
            )

    @staticmethod
    async def update_user_credentials(db: AsyncSession, user_id: int, updated_data: UserCredentialUpdate):
        try:
            user = await UserRepository.get_user_by_id(db, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found"
                )

            if user.password != updated_data.old_password:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Old password does not match"
                )

            updated_user = await UserRepository.update_user_credentials(db, user_id, updated_data)
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to update credentials for user {user_id}"
                )

            return updated_user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error updating credentials for user {user_id}: {e}"
            )
    
    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int):
        try:
            deleted = await UserRepository.delete_user(db, user_id)
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found"
                )
            return {"detail": "User deleted successfully"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error deleting user {user_id}: {e}"
            )
            
class UserActivityService:
    @staticmethod
    async def log_user_activity(db: AsyncSession, user_id: int, data: UserActivityCreate):
        try:
            activity = await UserRepository.log_user_activity(db, user_id, data)
            if not activity:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to log user activity"
                )
            return activity
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error logging activity for user {user_id}: {e}"
            )
            
    @staticmethod
    async def get_user_activities(db: AsyncSession, user_id: int):
        try:
            activities = await UserRepository.get_user_activities(db, user_id)
            return activities
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving activities for user {user_id}: {e}"
            )