from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from backend.models.user import Rank
from repository.user_repository import UserRepository
from schema.user_schema import UserUpdate, UserCredentialUpdate
from schema.authentication_schema import UserRegister

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
        except HTTPException:
            raise
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
        except HTTPException:
            raise
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
        except HTTPException:
            raise
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
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving user by username {username}: {e}"
            )

    @staticmethod
    async def add_eco_points(db: AsyncSession, user_id: int, points: int):
        try:
            if points <= 0:
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

            user_update = UserUpdate()
            user_update.eco_points = (user.eco_points or 0) + points

            if user_update.eco_points <= 500:
                user_update.rank = Rank.bronze
            elif user_update.eco_points <= 2000:
                user_update.rank = Rank.silver
            elif user_update.eco_points <= 5000:
                user_update.rank = Rank.gold
            elif user_update.eco_points <= 10000:
                user_update.rank = Rank.platinum
            else:
                user_update.rank = Rank.diamond

            updated_user = await UserRepository.update_user(db, user_id, user_update)
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to update eco points for user {user_id}"
                )

            return updated_user
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error updating eco points for user {user_id}: {e}"
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
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error updating credentials for user {user_id}: {e}"
            )
