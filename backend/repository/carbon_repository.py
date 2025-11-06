from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from models.carbon import CarbonEmission, VehicleType, FuelType
from datetime import date, datetime, timedelta
from schemas.carbon_schema import CarbonEmissionCreate, CarbonEmissionUpdate

class CarbonRepository:
    @staticmethod
    async def get_carbon_emission_by_id(db: AsyncSession, emission_id: int, user_id: int):
        try:
            result = await db.execute(
                select(CarbonEmission).where(
                    CarbonEmission.id == emission_id,
                    CarbonEmission.user_id == user_id
                )
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error retrieving carbon emission ID {emission_id}: {e}")
            return None

    @staticmethod
    async def get_carbon_emissions_by_user(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(
                select(CarbonEmission).where(CarbonEmission.user_id == user_id)
                .order_by(CarbonEmission.calculated_at.desc())
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error fetching carbon emissions for user ID {user_id}: {e}")
            return []

    @staticmethod
    async def get_total_carbon_by_user(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(
                select(func.sum(CarbonEmission.carbon_emission_kg))
                .where(CarbonEmission.user_id == user_id)
            )
            total = result.scalar()
            return total if total else 0.0
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error calculating total carbon emissions for user ID {user_id}: {e}")
            return 0.0
        
    @staticmethod
    async def get_total_carbon_by_day(db: AsyncSession, user_id: int, date: datetime):
        try:
            start_of_day = datetime(date.year, date.month, date.day)
            end_of_day = start_of_day + timedelta(days=1)
            result = await db.execute(
                select(func.sum(CarbonEmission.carbon_emission_kg))
                .where(
                    CarbonEmission.user_id == user_id,
                    CarbonEmission.calculated_at >= start_of_day,
                    CarbonEmission.calculated_at < end_of_day
                )
            )
            total = result.scalar()
            return total if total else 0.0
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error calculating total carbon emissions for user ID {user_id} on {date.date()}: {e}")
            return 0.0
        
    @staticmethod
    async def get_total_carbon_by_week(db: AsyncSession, user_id: int, date: datetime):
        try:
            start_of_week = datetime(date.year, date.month, date.day)
            end_of_week = start_of_week + timedelta(days=7)
            result = await db.execute(
                select(func.sum(CarbonEmission.carbon_emission_kg))
                .where(
                    CarbonEmission.user_id == user_id,
                    CarbonEmission.calculated_at >= start_of_week,
                    CarbonEmission.calculated_at < end_of_week
                )
            )
            total = result.scalar()
            return total if total else 0.0
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error calculating total carbon emissions for user ID {user_id} for week from {start_of_week.date()} to {end_of_week.date()}: {e}")
            return 0.0
        
    @staticmethod
    async def get_total_carbon_by_month(db: AsyncSession, user_id: int, start_of_month: datetime, end_of_month: datetime):
        try:
            result = await db.execute(
                select(func.sum(CarbonEmission.carbon_emission_kg))
                .where(
                    CarbonEmission.user_id == user_id,
                    CarbonEmission.calculated_at >= start_of_month,
                    CarbonEmission.calculated_at < end_of_month
                )
            )
            total = result.scalar()
            return total if total else 0.0
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error calculating total carbon emissions for user ID {user_id} for month {date.month}/{date.year}: {e}")
            return 0.0
        
    @staticmethod
    async def get_total_carbon_by_year(db: AsyncSession, user_id: int, year: int):
        try:
            start_of_year = datetime(year, 1, 1)
            end_of_year = datetime(year + 1, 1, 1)
            result = await db.execute(
                select(func.sum(CarbonEmission.carbon_emission_kg))
                .where(
                    CarbonEmission.user_id == user_id,
                    CarbonEmission.calculated_at >= start_of_year,
                    CarbonEmission.calculated_at < end_of_year
                )
            )
            total = result.scalar()
            return total if total else 0.0
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error calculating total carbon emissions for user ID {user_id} for year {year}: {e}")
            return 0.0
        
    @staticmethod
    async def get_total_carbon_by_date_range(db: AsyncSession, user_id: int, start_date: datetime, end_date: datetime):
        try:
            result = await db.execute(
                select(func.sum(CarbonEmission.carbon_emission_kg))
                .where(
                    CarbonEmission.user_id == user_id,
                    CarbonEmission.calculated_at >= start_date,
                    CarbonEmission.calculated_at < end_date
                )
            )
            total = result.scalar()
            return total if total else 0.0
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error calculating total carbon emissions for user ID {user_id} from {start_date.date()} to {end_date.date()}: {e}")
            return 0.0

    @staticmethod
    async def create_carbon_emission(db: AsyncSession, user_id: int, request: CarbonEmissionCreate, carbon_emission_kg: float):
        try:
            new_emission = CarbonEmission(
                user_id=user_id,
                vehicle_type=request.vehicle_type,
                distance_km=request.distance_km,
                fuel_type=request.fuel_type,
                carbon_emission_kg=carbon_emission_kg
            )
            db.add(new_emission)
            await db.commit()
            await db.refresh(new_emission)
            return new_emission
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error creating carbon emission record: {e}")
            return None
        
    @staticmethod
    async def update_carbon_emission(db: AsyncSession, emission_id: int, updated_data: CarbonEmissionUpdate, carbon_emission_kg: float):
        try:
            result = await db.execute(
                select(CarbonEmission).where(
                    CarbonEmission.id == emission_id
                )
            )
            emission = result.scalar_one_or_none()
            if not emission:
                print(f"Carbon emission ID {emission_id} not found")
                return None

            if updated_data.vehicle_type is not None:
                emission.vehicle_type = updated_data.vehicle_type
            if updated_data.distance_km is not None:
                emission.distance_km = updated_data.distance_km
            if updated_data.fuel_type is not None:
                emission.fuel_type = updated_data.fuel_type
            emission.carbon_emission_kg = carbon_emission_kg

            db.add(emission)
            await db.commit()
            await db.refresh(emission)
            return emission
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error updating carbon emission ID {emission_id}: {e}")
            return None

    @staticmethod
    async def delete_carbon_emission(db: AsyncSession, emission_id: int, user_id: int):
        try:
            result = await db.execute(
                select(CarbonEmission).where(
                    CarbonEmission.id == emission_id,
                    CarbonEmission.user_id == user_id
                )
            )
            emission = result.scalar_one_or_none()
            if not emission:
                print(f"Carbon emission ID {emission_id} not found")
                return False

            await db.delete(emission)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error deleting carbon emission ID {emission_id}: {e}")
            return False
