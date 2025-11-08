from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from models.plan import Plan, PlanDestination
from schemas.plan_schema import PlanRequestCreate, PlanRequestUpdate

class PlanRepository:
    @staticmethod
    async def get_plan_by_user_id(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(select(Plan).where(Plan.user_id == user_id))
            return result.scalars().all()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error retrieving plans for user ID {user_id}: {e}")
            return None

    @staticmethod
    async def create_plan(db: AsyncSession, user_id: int, plan_data: PlanRequestCreate):
        try:
            new_plan = Plan(
                user_id=user_id,
                place_name=plan_data.place_name,
                start_date=plan_data.start_date,
                end_date=plan_data.end_date,
                budget_limit=plan_data.budget_limit
            )
            db.add(new_plan)
            await db.commit()
            await db.refresh(new_plan)
            return new_plan
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error creating plan: {e}")
            return None

    @staticmethod
    async def update_plan(db: AsyncSession, plan_id: int, updated_data: PlanRequestUpdate):
        try:
            result = await db.execute(select(Plan).where(Plan.id == plan_id))
            plan = result.scalar_one_or_none()
            if not plan:
                print(f"Plan ID {plan_id} not found")
                return None

            if updated_data.place_name is not None:
                plan.place_name = updated_data.place_name
            if updated_data.start_date is not None:
                plan.start_date = updated_data.start_date
            if updated_data.end_date is not None:
                plan.end_date = updated_data.end_date
            if updated_data.budget_limit is not None:
                plan.budget_limit = updated_data.budget_limit

            db.add(plan)
            await db.commit()
            await db.refresh(plan)
            return plan
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error updating plan ID {plan_id}: {e}")
            return None
        
    @staticmethod
    async def delete_plan(db: AsyncSession, plan_id: int):
        try:
            result = await db.execute(select(Plan).where(Plan.id == plan_id))
            plan = result.scalar_one_or_none()
            if not plan:
                print(f"Plan ID {plan_id} not found")
                return False

            await db.delete(plan)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error deleting plan ID {plan_id}: {e}")
            return False

    @staticmethod
    async def get_plan_destinations(db: AsyncSession, plan_id: int):
        """Get all destinations for a specific plan"""
        try:
            result = await db.execute(
                select(PlanDestination).where(PlanDestination.plan_id == plan_id)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error retrieving destinations for plan ID {plan_id}: {e}")
            return []

    @staticmethod
    async def add_destination_to_plan(db: AsyncSession, plan_id: int, destination_id: int, 
                                     destination_type: str, visit_date, note: str = None):
        try:
            new_plan_dest = PlanDestination(
                plan_id=plan_id,
                destination_id=destination_id,
                type=destination_type,
                visit_date=visit_date,
                note=note
            )
            db.add(new_plan_dest)
            await db.commit()
            await db.refresh(new_plan_dest)
            return new_plan_dest
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error adding destination {destination_id} to plan {plan_id}: {e}")
            return None

    @staticmethod
    async def remove_destination_from_plan(db: AsyncSession, plan_destination_id: int):
        """Remove a destination from a plan"""
        try:
            result = await db.execute(
                select(PlanDestination).where(PlanDestination.id == plan_destination_id)
            )
            plan_dest = result.scalar_one_or_none()
            if not plan_dest:
                print(f"PlanDestination ID {plan_destination_id} not found")
                return False

            await db.delete(plan_dest)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error removing plan destination ID {plan_destination_id}: {e}")
            return False