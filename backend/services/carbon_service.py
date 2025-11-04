from fastapi import HTTPException, status
from repository.carbon_repository import CarbonRepository
from sqlalchemy.ext.asyncio import AsyncSession
from schema.carbon_schema import CarbonEmissionCreate, CarbonEmissionResponse, CarbonEmissionUpdate
from models.carbon import VehicleType, FuelType
from datetime import datetime, timedelta
from backend.integration.text_generator_api import get_text_generator

class CarbonService:
    EMISSION_FACTORS = {
        (VehicleType.car, FuelType.petrol): 0.171,
        (VehicleType.car, FuelType.diesel): 0.158,
        (VehicleType.car, FuelType.electric): 0.053,
        (VehicleType.car, FuelType.hybrid): 0.112,
        (VehicleType.bus, FuelType.petrol): 0.089,
        (VehicleType.bus, FuelType.diesel): 0.082,
        (VehicleType.bus, FuelType.electric): 0.027,
        (VehicleType.bus, FuelType.hybrid): 0.056,
        (VehicleType.motorbike, FuelType.petrol): 0.103,
        (VehicleType.motorbike, FuelType.electric): 0.024,
        (VehicleType.walk_or_cycle, FuelType.none): 0.0,
    }

    @staticmethod
    def calculate_carbon_emission(vehicle_type: VehicleType, distance_km: float, fuel_type: FuelType) -> float:
        emission_factor = CarbonService.EMISSION_FACTORS.get((vehicle_type, fuel_type), 0.0)
        return round(emission_factor * distance_km, 3)
    
    @staticmethod
    async def create_carbon_emission(db: AsyncSession, user_id: int, create_data: CarbonEmissionCreate):
        try:
            carbon_emission_kg = CarbonService.calculate_carbon_emission(
                create_data.vehicle_type,
                create_data.distance_km,
                create_data.fuel_type
            )
            new_emission = await CarbonRepository.create_carbon_emission(db, user_id, create_data, carbon_emission_kg)
            if not new_emission:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create carbon emission record"
                )
            return new_emission
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error creating carbon emission record: {e}"
            )
    
    @staticmethod
    async def get_carbon_emission_by_id(db: AsyncSession, emission_id: int, user_id: int):
        try:
            emission = await CarbonRepository.get_carbon_emission_by_id(db, emission_id, user_id)
            if not emission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Carbon emission record with ID {emission_id} not found"
                )
            return emission
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving carbon emission ID {emission_id}: {e}"
            )

    @staticmethod
    async def get_user_carbon_emissions(db: AsyncSession, user_id: int):
        try:
            emissions = await CarbonRepository.get_carbon_emissions_by_user(db, user_id)
            return emissions
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving carbon emissions for user ID {user_id}: {e}"
            )

    @staticmethod
    async def get_total_carbon_by_user(db: AsyncSession, user_id: int):
        try:
            total = await CarbonRepository.get_total_carbon_by_user(db, user_id)
            return {"user_id": user_id, "total_carbon_emission_kg": total}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error calculating total carbon emissions for user ID {user_id}: {e}"
            )

    @staticmethod
    async def get_total_carbon_by_day(db: AsyncSession, user_id: int, date: datetime):
        try:
            total = await CarbonRepository.get_total_carbon_by_day(db, user_id, date)
            return {"user_id": user_id, "total_carbon_emission_kg": total}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error calculating total carbon emissions for user ID {user_id} for day of {date}: {e}"
            )

    @staticmethod
    async def get_total_carbon_by_week(db: AsyncSession, user_id: int, date: datetime):
        try:
            start_of_week = date - timedelta(days=date.weekday())
            total = await CarbonRepository.get_total_carbon_by_week(db, user_id, start_of_week)
            return {"user_id": user_id, "total_carbon_emission_kg": total}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error calculating total carbon emissions for user ID {user_id} for week of {date}: {e}"
            )
        
    @staticmethod
    async def get_total_carbon_by_month(db: AsyncSession, user_id: int, date: datetime):
        try:
            start_of_month = datetime(date.year, date.month, 1)
            end_of_month = datetime(date.year, date.month + 1, 1) if date.month < 12 else datetime(date.year + 1, 1, 1)
            total = await CarbonRepository.get_total_carbon_by_month(db, user_id, start_of_month, end_of_month)
            return {"user_id": user_id, "total_carbon_emission_kg": total}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error calculating total carbon emissions for user ID {user_id} for month {date.month}/{date.year}: {e}"
            )

    @staticmethod
    async def get_total_carbon_by_year(db: AsyncSession, user_id: int, year: int):
        try:
            total = await CarbonRepository.get_total_carbon_by_year(db, user_id, year)
            return {"user_id": user_id, "total_carbon_emission_kg": total}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error calculating total carbon emissions for user ID {user_id} for year {year}: {e}"
            )
        
    @staticmethod
    async def get_total_carbon_by_date_range(db: AsyncSession, user_id: int, start_date: datetime, end_date: datetime):
        try:
            total = await CarbonRepository.get_total_carbon_by_date_range(db, user_id, start_date, end_date)
            return {"user_id": user_id, "total_carbon_emission_kg": total}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error calculating total carbon emissions for user ID {user_id} from {start_date} to {end_date}: {e}"
            )

    @staticmethod
    async def update_carbon_emission(db: AsyncSession, emission_id: int, user_id: int, updated_data: CarbonEmissionUpdate):
        try:
            existing_emission = await CarbonRepository.get_carbon_emission_by_id(db, emission_id, user_id)
            if not existing_emission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Carbon emission record with ID {emission_id} not found"
                )
            
            vehicle_type = updated_data.vehicle_type if updated_data.vehicle_type is not None else existing_emission.vehicle_type
            distance_km = updated_data.distance_km if updated_data.distance_km is not None else existing_emission.distance_km
            fuel_type = updated_data.fuel_type if updated_data.fuel_type is not None else existing_emission.fuel_type
            
            carbon_emission_kg = CarbonService.calculate_carbon_emission(vehicle_type, distance_km, fuel_type)
            
            updated_emission = await CarbonRepository.update_carbon_emission(db, emission_id, updated_data, carbon_emission_kg)
            if not updated_emission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Carbon emission record with ID {emission_id} not found"
                )
            return updated_emission
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error updating carbon emission ID {emission_id}: {e}"
            )

    @staticmethod
    async def delete_carbon_emission(db: AsyncSession, emission_id: int, user_id: int):
        try:
            success = await CarbonRepository.delete_carbon_emission(db, emission_id, user_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Carbon emission record with ID {emission_id} not found"
                )
            return {"detail": "Carbon emission record deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error deleting carbon emission ID {emission_id}: {e}"
            )
    
    async def generate_carbon_notification(self, user_id: int, carbon_emission_kg: float) -> str:
        text_generator = get_text_generator()
        prompt = (
            f"Generate a motivational notification for a user who has just recorded a carbon emission of "
            f"{carbon_emission_kg} kg CO2. Encourage them to reduce their carbon footprint and suggest "
            f"ways they can make more sustainable choices in their travel habits."
        )
        return await text_generator.generate_text(prompt)