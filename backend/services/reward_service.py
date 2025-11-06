import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from schemas.reward_schema import MissionCreate, MissionUpdate
from repository.mission_repository import MissionRepository, UserMissionRepository

class RewardService:
    @staticmethod
    async def get_all_missions(db: AsyncSession):
        try:
            missions = await MissionRepository.get_all_missions(db)
            return missions
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving all missions: {e}"
            )
        
    @staticmethod
    async def get_mission_by_id(db: AsyncSession, mission_id: int):
        try:
            mission = await MissionRepository.get_mission_by_id(db, mission_id)
            if not mission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Mission with ID {mission_id} not found"
                )
            return mission
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving mission by ID {mission_id}: {e}"
            )
    
    @staticmethod
    async def get_mission_by_name(db: AsyncSession, name: str):
        try:
            mission = await MissionRepository.get_mission_by_name(db, name)
            if not mission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Mission with name '{name}' not found"
                )
            return mission
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving mission by name '{name}': {e}"
            )
        
    @staticmethod
    async def update_mission(db: AsyncSession, mission_id: int, updated_data: MissionUpdate):
        try:
            mission = await MissionRepository.get_mission_by_id(db, mission_id)
            if not mission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Mission with ID {mission_id} not found"
                )

            updated_mission = await MissionRepository.update_mission(db, mission_id, updated_data)
            if not updated_mission:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update mission"
                )
            return updated_mission
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error updating mission ID {mission_id}: {e}"
            )

    @staticmethod
    async def create_mission(db: AsyncSession, mission_data: MissionCreate):
        try:
            existing_mission = await MissionRepository.get_mission_by_name(db, mission_data.name)
            if existing_mission:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Mission with name '{mission_data.name}' already exists"
                )

            new_mission = await MissionRepository.create_mission(db, mission_data)
            if not new_mission:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create mission"
                )
            return new_mission
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error creating mission: {e}"
            )
        
    @staticmethod
    async def all_completed_missions(db: AsyncSession, user_id: int):
        try:
            completed_missions = await UserMissionRepository.get_all_missions_by_user(db, user_id)
            return completed_missions
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving completed missions for user {user_id}: {e}"
            )
        
    @staticmethod
    async def complete_mission(db: AsyncSession, user_id: int, mission_id: int):
        try:
            mission = await MissionRepository.get_mission_by_id(db, mission_id)
            if not mission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Mission with ID {mission_id} not found"
                )

            already_completed = await UserMissionRepository.completed_mission(db, user_id, mission_id)
            if already_completed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User {user_id} has already completed mission {mission_id}"
                )

            new_user_mission = await UserMissionRepository.add_mission_to_user(
                db,
                user_id=user_id,
                mission_id=mission_id
            )
            if not new_user_mission:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create user mission for user {user_id} and mission {mission_id}"
                )
            return new_user_mission
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error completing mission: {e}"
            )
        
    @staticmethod
    async def delete_mission(db: AsyncSession, mission_id: int):
        try:
            mission = await MissionRepository.get_mission_by_id(db, mission_id)
            if not mission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Mission with ID {mission_id} not found"
                )

            success = await MissionRepository.delete_mission(db, mission_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete mission"
                )
            return {"detail": "Mission deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error deleting mission ID {mission_id}: {e}"
            )
        