from fastapi import HTTPException, status
from repository.carbon_repository import CarbonRepository
from sqlalchemy.ext.asyncio import AsyncSession
from schema.carbon_schema import CarbonEmissionCreate, CarbonEmissionResponse, CarbonEmissionUpdate
from models.carbon import VehicleType, FuelType
from datetime import datetime, timedelta
from integration.text_generator_api import get_text_generator

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
            current_total = await CarbonRepository.get_total_carbon_by_day(db, user_id, date)
            
            previous_date = date - timedelta(days=1)
            previous_total = await CarbonRepository.get_total_carbon_by_day(db, user_id, previous_date)
            
            difference = current_total - previous_total
            percentage_change = ((difference / previous_total) * 100) if previous_total > 0 else 0
            
            text_generator = get_text_generator()
            if difference < 0:
                prompt = (
                    f"Write a short congratulatory message (2-3 sentences) for a user who reduced their carbon emissions "
                    f"from {previous_total:.2f} kg CO2 yesterday to {current_total:.2f} kg CO2 today "
                    f"(a {abs(percentage_change):.1f}% decrease). Encourage them to keep up the great work."
                )
            elif difference > 0:
                prompt = (
                    f"Write a short gentle reminder (2-3 sentences) for a user whose carbon emissions increased "
                    f"from {previous_total:.2f} kg CO2 yesterday to {current_total:.2f} kg CO2 today "
                    f"(a {percentage_change:.1f}% increase). Suggest simple eco-friendly actions like using public transport, "
                    f"cycling, or carpooling."
                )
            else:
                prompt = (
                    f"Write a short neutral message (2-3 sentences) for a user who maintained the same carbon emissions "
                    f"of {current_total:.2f} kg CO2 for two consecutive days. Encourage them to try reducing it further."
                )
            
            motivational_message = await text_generator.generate_text(prompt)
            
            return {
                "user_id": user_id,
                "date": date.strftime("%Y-%m-%d"),
                "total_carbon_emission_kg": current_total,
                "previous_day_total": previous_total,
                "difference": difference,
                "percentage_change": round(percentage_change, 2),
                "message": motivational_message
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error calculating total carbon emissions for user ID {user_id} for day of {date}: {e}"
            )

    @staticmethod
    async def get_total_carbon_by_week(db: AsyncSession, user_id: int, date: datetime):
        try:
            start_of_week = date - timedelta(days=date.weekday())
            current_total = await CarbonRepository.get_total_carbon_by_week(db, user_id, start_of_week)
            
            start_of_previous_week = start_of_week - timedelta(days=7)
            previous_total = await CarbonRepository.get_total_carbon_by_week(db, user_id, start_of_previous_week)
            
            difference = current_total - previous_total
            percentage_change = ((difference / previous_total) * 100) if previous_total > 0 else 0
            
            text_generator = get_text_generator()
            if difference < 0:
                prompt = (
                    f"Write a short congratulatory message (2-3 sentences) for a user who reduced their weekly carbon emissions "
                    f"from {previous_total:.2f} kg CO2 last week to {current_total:.2f} kg CO2 this week "
                    f"(a {abs(percentage_change):.1f}% decrease). Celebrate their eco-friendly choices and motivate them to continue."
                )
            elif difference > 0:
                prompt = (
                    f"Write a short gentle reminder (2-3 sentences) for a user whose weekly carbon emissions increased "
                    f"from {previous_total:.2f} kg CO2 last week to {current_total:.2f} kg CO2 this week "
                    f"(a {percentage_change:.1f}% increase). Suggest sustainable alternatives like public transportation, "
                    f"walking, or combining trips."
                )
            else:
                prompt = (
                    f"Write a short message (2-3 sentences) for a user who maintained {current_total:.2f} kg CO2 emissions "
                    f"for two consecutive weeks. Encourage them to challenge themselves to reduce it next week."
                )
            
            motivational_message = await text_generator.generate_text(prompt)
            
            return {
                "user_id": user_id,
                "week_starting": start_of_week.strftime("%Y-%m-%d"),
                "total_carbon_emission_kg": current_total,
                "previous_week_total": previous_total,
                "difference": difference,
                "percentage_change": round(percentage_change, 2),
                "message": motivational_message
            }
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
            current_total = await CarbonRepository.get_total_carbon_by_month(db, user_id, start_of_month, end_of_month)
            
            if date.month == 1:
                start_of_previous_month = datetime(date.year - 1, 12, 1)
                end_of_previous_month = datetime(date.year, 1, 1)
            else:
                start_of_previous_month = datetime(date.year, date.month - 1, 1)
                end_of_previous_month = datetime(date.year, date.month, 1)
            
            previous_total = await CarbonRepository.get_total_carbon_by_month(db, user_id, start_of_previous_month, end_of_previous_month)
            
            difference = current_total - previous_total
            percentage_change = ((difference / previous_total) * 100) if previous_total > 0 else 0
            
            text_generator = get_text_generator()
            if difference < 0:
                prompt = (
                    f"Write a short congratulatory message (2-3 sentences) for a user who reduced their monthly carbon emissions "
                    f"from {previous_total:.2f} kg CO2 last month to {current_total:.2f} kg CO2 this month "
                    f"(a {abs(percentage_change):.1f}% decrease). Praise their commitment to sustainability and inspire them to maintain this trend."
                )
            elif difference > 0:
                prompt = (
                    f"Write a short gentle reminder (2-3 sentences) for a user whose monthly carbon emissions increased "
                    f"from {previous_total:.2f} kg CO2 last month to {current_total:.2f} kg CO2 this month "
                    f"(a {percentage_change:.1f}% increase). Suggest planning eco-friendly travel routes, using greener transportation, "
                    f"or tracking daily emissions more carefully."
                )
            else:
                prompt = (
                    f"Write a short message (2-3 sentences) for a user who maintained {current_total:.2f} kg CO2 emissions "
                    f"for two consecutive months. Encourage them to set new reduction goals for next month."
                )
            
            motivational_message = await text_generator.generate_text(prompt)
            
            return {
                "user_id": user_id,
                "month": f"{date.year}-{date.month:02d}",
                "total_carbon_emission_kg": current_total,
                "previous_month_total": previous_total,
                "difference": difference,
                "percentage_change": round(percentage_change, 2),
                "message": motivational_message
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error calculating total carbon emissions for user ID {user_id} for month {date.month}/{date.year}: {e}"
            )

    @staticmethod
    async def get_total_carbon_by_year(db: AsyncSession, user_id: int, year: int):
        try:
            current_total = await CarbonRepository.get_total_carbon_by_year(db, user_id, year)
            
            previous_year = year - 1
            previous_total = await CarbonRepository.get_total_carbon_by_year(db, user_id, previous_year)
            
            difference = current_total - previous_total
            percentage_change = ((difference / previous_total) * 100) if previous_total > 0 else 0
            
            text_generator = get_text_generator()
            if difference < 0:
                prompt = (
                    f"Write a short congratulatory message (2-3 sentences) for a user who reduced their annual carbon emissions "
                    f"from {previous_total:.2f} kg CO2 in {previous_year} to {current_total:.2f} kg CO2 in {year} "
                    f"(a {abs(percentage_change):.1f}% decrease). Celebrate this impressive achievement and their dedication to fighting climate change."
                )
            elif difference > 0:
                prompt = (
                    f"Write a short gentle reminder (2-3 sentences) for a user whose annual carbon emissions increased "
                    f"from {previous_total:.2f} kg CO2 in {previous_year} to {current_total:.2f} kg CO2 in {year} "
                    f"(a {percentage_change:.1f}% increase). Encourage them to set concrete goals for the new year, "
                    f"such as using electric vehicles, public transport more often, or offsetting emissions."
                )
            else:
                prompt = (
                    f"Write a short message (2-3 sentences) for a user who maintained {current_total:.2f} kg CO2 emissions "
                    f"for two consecutive years. Challenge them to make meaningful reductions in the coming year."
                )
            
            motivational_message = await text_generator.generate_text(prompt)
            
            return {
                "user_id": user_id,
                "year": year,
                "total_carbon_emission_kg": current_total,
                "previous_year_total": previous_total,
                "difference": difference,
                "percentage_change": round(percentage_change, 2),
                "message": motivational_message
            }
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

    async def generate_carbon_notification(self, carbon_emission_kg: float) -> str:
        text_generator = get_text_generator()
        prompt = (
            f"Generate a motivational notification for a user who has just recorded a carbon emission of "
            f"{carbon_emission_kg} kg CO2. Encourage them to reduce their carbon footprint and suggest "
            f"ways they can make more sustainable choices in their travel habits."
        )
        return await text_generator.generate_text(prompt)