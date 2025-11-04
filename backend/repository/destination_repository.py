from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from models.destination import Destination
from schema.destination_schema import DestinationCreate, DestinationUpdate

# Note: This repository uses the destination database (get_destination_db)
# All methods expect AsyncSession from DestinationAsyncSessionLocal

class DestinationRepository:       
    @staticmethod
    async def get_destination_by_id(db: AsyncSession, destination_id: int):
        try:
            result = await db.execute(select(Destination).where(Destination.id == destination_id))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error retrieving destination by ID {destination_id}: {e}")
            return None

    @staticmethod
    async def get_destination_by_lon_and_lat(db: AsyncSession, longitude: float, latitude: float):
        try:
            result = await db.execute(select(Destination).where(Destination.longitude == longitude, Destination.latitude == latitude))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error retrieving destination by longitude {longitude} and latitude {latitude}: {e}")
            return None
        
    @staticmethod
    async def create_destination(db: AsyncSession, destination: DestinationCreate):
        try:
            new_destination = Destination(
                longitude=destination.longitude,
                latitude=destination.latitude
            )
            db.add(new_destination)
            await db.commit()
            await db.refresh(new_destination)
            return new_destination
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error creating destination: {e}")
            return None

    @staticmethod
    async def update_destination(db: AsyncSession, destination_id: int, updated_data: DestinationUpdate):
        try:
            destination = await DestinationRepository.get_destination_by_id(db, destination_id)
            if not destination:
                print(f"Destination with ID {destination_id} not found")
                return None

            if updated_data.longitude is not None:
                destination.longitude = updated_data.longitude
            if updated_data.latitude is not None:
                destination.latitude = updated_data.latitude

            db.add(destination)
            await db.commit()
            await db.refresh(destination)
            return destination
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error updating destination ID {destination_id}: {e}")
            return None
        
    @staticmethod
    async def delete_destination(db: AsyncSession, destination_id: int):
        try:
            destination = await DestinationRepository.get_destination_by_id(db, destination_id)
            if not destination:
                print(f"Destination with ID {destination_id} not found")
                return False

            await db.delete(destination)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error deleting destination ID {destination_id}: {e}")
            return False