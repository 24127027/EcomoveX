from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import Rank
from repository.user_repository import UserRepository
from services.storage_service import StorageService
from schemas.user_schema import *

class UserService:
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> UserResponse:
        try:
            user = await UserRepository.get_user_by_id(db, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found"
                )
            
            avt_url = None
            cover_url = None
            if user.avt_blob_name:
                avt_url = await StorageService.generate_signed_url(user.avt_blob_name)
            if user.cover_blob_name:
                cover_url = await StorageService.generate_signed_url(user.cover_blob_name)
            return UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                eco_point=user.eco_point,
                rank=user.rank,
                role=user.role,
                avt_url=avt_url if user.avt_blob_name else None,
                cover_url=cover_url if user.cover_blob_name else None,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving user by ID {user_id}: {e}"
            )

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> UserResponse:
        try:
            user = await UserRepository.get_user_by_email(db, email)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with email '{email}' not found"
                )
            
            avt_url = None
            cover_url = None
            if user.avt_blob_name:
                avt_url = await StorageService.generate_signed_url(user.avt_blob_name)
            if user.cover_blob_name:
                cover_url = await StorageService.generate_signed_url(user.cover_blob_name)
            return UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                eco_point=user.eco_point,
                rank=user.rank,
                role=user.role,
                avt_url=avt_url if user.avt_blob_name else None,
                cover_url=cover_url if user.cover_blob_name else None,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving user by email {email}: {e}"
            )

    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> UserResponse:
        try:
            user = await UserRepository.get_user_by_username(db, username)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with username '{username}' not found"
                )
            
            avt_url = None
            cover_url = None
            if user.avt_blob_name:
                avt_url = await StorageService.generate_signed_url(user.avt_blob_name)
            if user.cover_blob_name:
                cover_url = await StorageService.generate_signed_url(user.cover_blob_name)
            return UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                eco_point=user.eco_point,
                rank=user.rank,
                role=user.role,
                avt_url=avt_url if user.avt_blob_name else None,
                cover_url=cover_url if user.cover_blob_name else None,
            )
        except HTTPException:
            raise
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
            
            avt_url = None
            cover_url = None
            if user.avt_blob_name:
                avt_url = await StorageService.generate_signed_url(user.avt_blob_name)
            if user.cover_blob_name:
                cover_url = await StorageService.generate_signed_url(user.cover_blob_name)

            new_point = (user.eco_point or 0) + point

            if new_point <= 500:
                new_rank = Rank.bronze
            elif new_point <= 2000:
                new_rank = Rank.silver
            elif new_point <= 5000:
                new_rank = Rank.gold
            elif new_point <= 10000:
                new_rank = Rank.platinum
            else:
                new_rank = Rank.diamond

            user_update = UserUpdateEcoPoint(point=new_point, rank=new_rank)

            updated_user = await UserRepository.add_eco_point(db, user_id, user_update)
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to update eco point for user {user_id}"
                )

            return UserResponse(
                id=updated_user.id,
                username=updated_user.username,
                email=updated_user.email,
                eco_point=updated_user.eco_point,
                rank=updated_user.rank,
                role=updated_user.role,
                avt_url=avt_url if user.avt_blob_name else None,
                cover_url=cover_url if user.cover_blob_name else None,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error adding eco point for user {user_id}: {e}"
            )
    
    @staticmethod
    async def get_users_by_ids(db: AsyncSession, user_ids: List[int]) -> List[UserResponse]:
        try:
            users = await UserRepository.get_users_by_ids(db, user_ids)
            
            user_responses = []
            for user in users:
                avt_url = None
                cover_url = None
                if user.avt_blob_name:
                    avt_url = await StorageService.generate_signed_url(user.avt_blob_name)
                if user.cover_blob_name:
                    cover_url = await StorageService.generate_signed_url(user.cover_blob_name)
                
                user_responses.append(UserResponse(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    eco_point=user.eco_point,
                    rank=user.rank,
                    role=user.role,
                    avt_url=avt_url if user.avt_blob_name else None,
                    cover_url=cover_url if user.cover_blob_name else None,
                ))
            
            return user_responses
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving users by IDs: {e}"
            )

    @staticmethod
    async def update_user_credentials(db: AsyncSession, user_id: int, updated_data: UserCredentialUpdate) -> UserResponse:
        try:
            user = await UserRepository.get_user_by_id(db, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found"
                )
            
            avt_url = None
            cover_url = None
            if user.avt_blob_name:
                avt_url = await StorageService.generate_signed_url(user.avt_blob_name)
            if user.cover_blob_name:
                cover_url = await StorageService.generate_signed_url(user.cover_blob_name)

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

            return UserResponse(
                id=updated_user.id,
                username=updated_user.username,
                email=updated_user.email,
                eco_point=updated_user.eco_point,
                rank=updated_user.rank,
                role=updated_user.role,
                avt_url=avt_url if user.avt_blob_name else None,
                cover_url=cover_url if user.cover_blob_name else None,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error updating credentials for user {user_id}: {e}"
            )
    
    @staticmethod
    async def update_user_profile(db: AsyncSession, user_id: int, updated_data: UserProfileUpdate) -> UserResponse:
        try:
            user = await UserRepository.get_user_by_id(db, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found"
                )
            avt_url = None
            cover_url = None
            if user.avt_blob_name:
                avt_url = await StorageService.generate_signed_url(user.avt_blob_name)
            if user.cover_blob_name:
                cover_url = await StorageService.generate_signed_url(user.cover_blob_name)

            updated_user = await UserRepository.update_user_profile(db, user_id, updated_data)
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to update profile for user {user_id}"
                )

            return UserResponse(
                id=updated_user.id,
                username=updated_user.username,
                email=updated_user.email,
                eco_point=updated_user.eco_point,
                rank=updated_user.rank,
                role=updated_user.role,
                avt_url=avt_url,
                cover_url=cover_url,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error updating profile for user {user_id}: {e}"
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
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error deleting user {user_id}: {e}"
            )
            
class UserActivityService:
    @staticmethod
    async def log_user_activity(db: AsyncSession, user_id: int, data: UserActivityCreate) -> UserActivityResponse:
        try:
            activity = await UserRepository.log_user_activity(db, user_id, data)
            if not activity:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to log user activity"
                )
            return UserActivityResponse(
                id=activity.id,
                user_id=activity.user_id,
                destination_id=activity.destination_id,
                activity=activity.activity,
                timestamp=activity.timestamp
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error logging activity for user {user_id}: {e}"
            )
            
    @staticmethod
    async def get_user_activities(db: AsyncSession, user_id: int)-> List[UserActivityResponse]:
        try:
            activities = await UserRepository.get_user_activities(db, user_id)
            activity_list = []
            for activity in activities:
                activity_list.append(
                    UserActivityResponse(
                        id=activity.id,
                        user_id=activity.user_id,
                        destination_id=activity.destination_id,
                        activity=activity.activity,
                        timestamp=activity.timestamp
                    )
                )
            return activity_list
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving activities for user {user_id}: {e}"
            )