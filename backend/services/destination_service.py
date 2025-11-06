from fastapi import HTTPException, status
from repository.destination_repository import DestinationRepository
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
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving destination ID {destination_id}: {e}"
            )
    
    @staticmethod
    async def get_destination_by_coordinates(db: AsyncSession, longitude: float, latitude: float):
        try:
            destination = await DestinationRepository.get_destination_by_lon_and_lat(db, longitude, latitude)
            if not destination:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Destination at coordinates ({longitude}, {latitude}) not found"
                )
            return destination
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving destination by coordinates: {e}"
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
        except HTTPException:
            raise
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
        except HTTPException:
            raise
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
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error deleting destination ID {destination_id}: {e}"
            )
