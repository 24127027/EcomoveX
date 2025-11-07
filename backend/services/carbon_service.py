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
            current_emissions = await CarbonRepository.get_carbon_emissions_by_user(db, user_id)
            current_day_data = [
                {
                    "vehicle_type": e.vehicle_type.value,
                    "fuel_type": e.fuel_type.value,
                    "distance_km": e.distance_km,
                    "carbon_emission_kg": e.carbon_emission_kg,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in current_emissions if e.timestamp.date() == date.date()
            ]
            
            previous_date = date - timedelta(days=1)
            previous_day_data = [
                {
                    "vehicle_type": e.vehicle_type.value,
                    "fuel_type": e.fuel_type.value,
                    "distance_km": e.distance_km,
                    "carbon_emission_kg": e.carbon_emission_kg,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in current_emissions if e.timestamp.date() == previous_date.date()
            ]
            
            text_generator = get_text_generator()
            prompt = f"""Analyze the following carbon emission data and provide a summary with a motivational message:

                Time Range: Daily comparison
                Current Day: {date.strftime("%Y-%m-%d")}
                Previous Day: {previous_date.strftime("%Y-%m-%d")}

                Current Day Data ({len(current_day_data)} trips):
                {current_day_data}

                Previous Day Data ({len(previous_day_data)} trips):
                {previous_day_data}

                Instructions:
                1. Calculate the total emissions for each day
                2. Compare the two days and determine the percentage change
                3. Analyze the types of transportation used
                4. Generate a short personalized message (2-3 sentences) that:
                - If emissions decreased: Congratulate the user and encourage them to keep it up
                - If emissions increased: Gently remind them and suggest eco-friendly alternatives
                - If emissions stayed the same: Encourage them to try reducing further
                5. Include specific insights about their travel patterns if relevant

                Format your response as a brief, friendly message."""

            summary_message = await text_generator.generate_text(prompt)
            
            return {
                "user_id": user_id,
                "date": date.strftime("%Y-%m-%d"),
                "summary": summary_message
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
            end_of_week = start_of_week + timedelta(days=6)
            
            start_of_previous_week = start_of_week - timedelta(days=7)
            end_of_previous_week = start_of_previous_week + timedelta(days=6)
            
            current_emissions = await CarbonRepository.get_carbon_emissions_by_user(db, user_id)
            
            current_week_data = [
                {
                    "vehicle_type": e.vehicle_type.value,
                    "fuel_type": e.fuel_type.value,
                    "distance_km": e.distance_km,
                    "carbon_emission_kg": e.carbon_emission_kg,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in current_emissions 
                if start_of_week.date() <= e.timestamp.date() <= end_of_week.date()
            ]
            
            previous_week_data = [
                {
                    "vehicle_type": e.vehicle_type.value,
                    "fuel_type": e.fuel_type.value,
                    "distance_km": e.distance_km,
                    "carbon_emission_kg": e.carbon_emission_kg,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in current_emissions 
                if start_of_previous_week.date() <= e.timestamp.date() <= end_of_previous_week.date()
            ]
            
            text_generator = get_text_generator()
            prompt = f"""Analyze the following carbon emission data and provide a summary with a motivational message:

                Time Range: Weekly comparison
                Current Week: {start_of_week.strftime("%Y-%m-%d")} to {end_of_week.strftime("%Y-%m-%d")}
                Previous Week: {start_of_previous_week.strftime("%Y-%m-%d")} to {end_of_previous_week.strftime("%Y-%m-%d")}

                Current Week Data ({len(current_week_data)} trips):
                {current_week_data}

                Previous Week Data ({len(previous_week_data)} trips):
                {previous_week_data}

                Instructions:
                1. Calculate the total emissions for each week
                2. Compare the two weeks and determine the percentage change
                3. Analyze the patterns: most common transportation types, daily distribution, etc.
                4. Generate a short personalized message (2-3 sentences) that:
                - If emissions decreased: Celebrate their eco-friendly choices and motivate them to continue
                - If emissions increased: Suggest sustainable alternatives like public transportation, walking, or combining trips
                - If emissions stayed the same: Challenge them to reduce it next week
                5. Provide actionable insights based on their weekly travel patterns

                Format your response as a brief, encouraging message."""

            summary_message = await text_generator.generate_text(prompt)
            
            return {
                "user_id": user_id,
                "week_starting": start_of_week.strftime("%Y-%m-%d"),
                "week_ending": end_of_week.strftime("%Y-%m-%d"),
                "summary": summary_message
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
            if date.month == 12:
                end_of_month = datetime(date.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_of_month = datetime(date.year, date.month + 1, 1) - timedelta(days=1)
            
            if date.month == 1:
                start_of_previous_month = datetime(date.year - 1, 12, 1)
                end_of_previous_month = datetime(date.year - 1, 12, 31)
            else:
                start_of_previous_month = datetime(date.year, date.month - 1, 1)
                end_of_previous_month = datetime(date.year, date.month, 1) - timedelta(days=1)
            
            current_emissions = await CarbonRepository.get_carbon_emissions_by_user(db, user_id)
            
            current_month_data = [
                {
                    "vehicle_type": e.vehicle_type.value,
                    "fuel_type": e.fuel_type.value,
                    "distance_km": e.distance_km,
                    "carbon_emission_kg": e.carbon_emission_kg,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in current_emissions 
                if start_of_month.date() <= e.timestamp.date() <= end_of_month.date()
            ]
            
            previous_month_data = [
                {
                    "vehicle_type": e.vehicle_type.value,
                    "fuel_type": e.fuel_type.value,
                    "distance_km": e.distance_km,
                    "carbon_emission_kg": e.carbon_emission_kg,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in current_emissions 
                if start_of_previous_month.date() <= e.timestamp.date() <= end_of_previous_month.date()
            ]
            
            text_generator = get_text_generator()
            prompt = f"""Analyze the following carbon emission data and provide a summary with a motivational message:

                Time Range: Monthly comparison
                Current Month: {start_of_month.strftime("%B %Y")} ({start_of_month.strftime("%Y-%m-%d")} to {end_of_month.strftime("%Y-%m-%d")})
                Previous Month: {start_of_previous_month.strftime("%B %Y")} ({start_of_previous_month.strftime("%Y-%m-%d")} to {end_of_previous_month.strftime("%Y-%m-%d")})

                Current Month Data ({len(current_month_data)} trips):
                {current_month_data}

                Previous Month Data ({len(previous_month_data)} trips):
                {previous_month_data}

                Instructions:
                1. Calculate the total emissions for each month
                2. Compare the two months and determine the percentage change
                3. Analyze monthly patterns: preferred transportation modes, peak emission days, trends
                4. Generate a short personalized message (2-3 sentences) that:
                - If emissions decreased: Praise their commitment to sustainability and inspire them to maintain this trend
                - If emissions increased: Suggest planning eco-friendly travel routes, using greener transportation, or tracking daily emissions more carefully
                - If emissions stayed the same: Encourage them to set new reduction goals for next month
                5. Provide monthly insights and actionable recommendations

                Format your response as a brief, motivational message."""

            summary_message = await text_generator.generate_text(prompt)
            
            return {
                "user_id": user_id,
                "month": f"{date.year}-{date.month:02d}",
                "summary": summary_message
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error calculating total carbon emissions for user ID {user_id} for month {date.month}/{date.year}: {e}"
            )

    @staticmethod
    async def get_total_carbon_by_year(db: AsyncSession, user_id: int, year: int):
        try:
            current_emissions = await CarbonRepository.get_carbon_emissions_by_user(db, user_id)
            
            current_year_data = [
                {
                    "vehicle_type": e.vehicle_type.value,
                    "fuel_type": e.fuel_type.value,
                    "distance_km": e.distance_km,
                    "carbon_emission_kg": e.carbon_emission_kg,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in current_emissions 
                if e.timestamp.year == year
            ]
            
            previous_year = year - 1
            previous_year_data = [
                {
                    "vehicle_type": e.vehicle_type.value,
                    "fuel_type": e.fuel_type.value,
                    "distance_km": e.distance_km,
                    "carbon_emission_kg": e.carbon_emission_kg,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in current_emissions 
                if e.timestamp.year == previous_year
            ]
            
            text_generator = get_text_generator()
            prompt = f"""Analyze the following carbon emission data and provide a summary with a motivational message:

                Time Range: Annual comparison
                Current Year: {year}
                Previous Year: {previous_year}

                Current Year Data ({len(current_year_data)} trips):
                {current_year_data}

                Previous Year Data ({len(previous_year_data)} trips):
                {previous_year_data}

                Instructions:
                1. Calculate the total emissions for each year
                2. Compare the two years and determine the percentage change
                3. Analyze annual patterns: seasonal trends, most/least eco-friendly months, transportation preferences
                4. Generate a short personalized message (2-3 sentences) that:
                - If emissions decreased: Celebrate this impressive achievement and their dedication to fighting climate change
                - If emissions increased: Encourage them to set concrete goals for the new year, such as using electric vehicles, public transport more often, or offsetting emissions
                - If emissions stayed the same: Challenge them to make meaningful reductions in the coming year
                5. Provide a year-in-review perspective with long-term recommendations

                Format your response as a brief, impactful message."""

            summary_message = await text_generator.generate_text(prompt)
            
            return {
                "user_id": user_id,
                "year": year,
                "summary": summary_message
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