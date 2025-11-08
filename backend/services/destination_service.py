from fastapi import HTTPException, status
from repository.destination_repository import DestinationRepository, UserSavedDestinationRepository
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.destination_schema import DestinationCreate, DestinationUpdate

class DestinationService:
    @staticmethod
    async def get_destination_by_id(db: AsyncSession, destination_id: int):
        try:
            destination = await DestinationRepository.get_destination_by_id(db, destination_id)
            if not destination:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Destination with ID {destination_id} not found"
                )
            return destination
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving destination ID {destination_id}: {e}"
            )
    
    @staticmethod
    async def create_destination(db: AsyncSession, destination_data: DestinationCreate):
        try:
            new_destination = await DestinationRepository.create_destination(db, destination_data)
            if not new_destination:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create destination"
                )
            return new_destination
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error creating destination: {e}"
            )
    
    @staticmethod
    async def update_destination(db: AsyncSession, destination_id: int, updated_data: DestinationUpdate):
        try:
            updated_destination = await DestinationRepository.update_destination(db, destination_id, updated_data)
            if not updated_destination:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Destination with ID {destination_id} not found"
                )
            return updated_destination
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error updating destination ID {destination_id}: {e}"
            )
    
    @staticmethod
    async def delete_destination(db: AsyncSession, destination_id: int):
        try:
            success = await DestinationRepository.delete_destination(db, destination_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Destination with ID {destination_id} not found"
                )
            return {"detail": "Destination deleted successfully"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error deleting destination ID {destination_id}: {e}"
            )

class UserSavedDestinationService:  
    @staticmethod
    async def save_destination_for_user(db: AsyncSession, user_id: int, destination_id: int):
        try:
            saved = await UserSavedDestinationRepository.save_destination_for_user(db, user_id, destination_id)
            if not saved:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to save destination for user"
                )
            return saved
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error saving destination for user ID {user_id}: {e}"
            )
            
    @staticmethod
    async def get_saved_destinations_for_user(db: AsyncSession, user_id: int):
        try:
            saved_destinations = await UserSavedDestinationRepository.get_saved_destinations_for_user(db, user_id)
            return saved_destinations
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving saved destinations for user ID {user_id}: {e}"
            )
            
    @staticmethod
    async def delete_saved_destination(db: AsyncSession, user_id: int, destination_id: int):
        try:
            success = await UserSavedDestinationRepository.delete_saved_destination(db, user_id, destination_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Saved destination not found for user"
                )
            return {"detail": "Saved destination deleted successfully"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error deleting saved destination for user ID {user_id} and destination ID {destination_id}: {e}"
            )
            
    @staticmethod
    async def is_saved_destination(db: AsyncSession, user_id: int, destination_id: int):
        try:
            saved_destinations = await UserSavedDestinationRepository.get_saved_destinations_for_user(db, user_id)
            for saved in saved_destinations:
                if saved.destination_id == destination_id:
                    return True
            return False
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error checking saved destination for user ID {user_id} and destination ID {destination_id}: {e}"
            )