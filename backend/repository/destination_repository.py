from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from models.destination import Destination, UserSavedDestination
from schemas.destination_schema import DestinationCreate, DestinationUpdate, UserSavedDestinationCreate, UserSavedDestinationResponse

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
        
class UserSavedDestinationRepository:
    @staticmethod
    async def save_destination_for_user(db: AsyncSession, user_id: int, destination_data: UserSavedDestinationCreate):
        try:
            new_saved_destination = UserSavedDestination(
                user_id=user_id,
                destination_id=destination_data.destination_id,
                note=destination_data.note or ""
            )
            db.add(new_saved_destination)
            await db.commit()
            await db.refresh(new_saved_destination)
            return new_saved_destination
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error saving destination for user ID {user_id}: {e}")
            return None
        
    @staticmethod
    async def get_saved_destinations_for_user(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(select(UserSavedDestination).where(UserSavedDestination.user_id == user_id))
            return result.scalars().all()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error retrieving saved destinations for user ID {user_id}: {e}")
            return []
        
    @staticmethod
    async def delete_saved_destination(db: AsyncSession, user_id: int, destination_id: int):
        try:
            result = await db.execute(
                select(UserSavedDestination).where(
                    UserSavedDestination.user_id == user_id,
                    UserSavedDestination.destination_id == destination_id
                )
            )
            saved_destination = result.scalar_one_or_none()
            if not saved_destination:
                print(f"Saved destination for user ID {user_id} and destination ID {destination_id} not found")
                return False
            await db.delete(saved_destination)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error deleting saved destination for user ID {user_id} and destination ID {destination_id}: {e}")
            return False

    @staticmethod
    async def is_saved_destination(db: AsyncSession, user_id: int, destination_id: int):
        try:
            result = await db.execute(
                select(UserSavedDestination).where(
                    UserSavedDestination.user_id == user_id,
                    UserSavedDestination.destination_id == destination_id
                )
            )
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error checking saved destination for user ID {user_id} and destination ID {destination_id}: {e}")
            return False