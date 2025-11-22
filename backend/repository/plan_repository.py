#=================================================
#Old planning repository code replaced with new planning
#=================================================



from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from models.plan import *
from schemas.plan_schema import *

class PlanRepository:
    @staticmethod
    async def get_plan_by_user_id(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(select(Plan).where(Plan.user_id == user_id))
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: retrieving plans for user ID {user_id} - {e}")
            return []
        
    @staticmethod
    async def get_plan_by_id(db: AsyncSession, plan_id: int):
        try:
            result = await db.execute(select(Plan).where(Plan.id == plan_id))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"ERROR: retrieving plan ID {plan_id} - {e}")
            return None

    @staticmethod
    async def create_plan(db: AsyncSession, user_id: int, plan_data: PlanCreate):
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
            print(f"ERROR: creating plan - {e}")
            return None

    @staticmethod
    async def update_plan(db: AsyncSession, plan_id: int, updated_data: PlanUpdate):
        try:
            result = await db.execute(select(Plan).where(Plan.id == plan_id))
            plan = result.scalar_one_or_none()
            if not plan:
                print(f"WARNING: WARNING: Plan ID {plan_id} not found")
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
            print(f"ERROR: updating plan ID {plan_id} - {e}")
            return None
        
    @staticmethod
    async def delete_plan(db: AsyncSession, plan_id: int):
        try:
            result = await db.execute(select(Plan).where(Plan.id == plan_id))
            plan = result.scalar_one_or_none()
            if not plan:
                print(f"WARNING: WARNING: Plan ID {plan_id} not found")
                return False

            await db.delete(plan)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: deleting plan ID {plan_id} - {e}")
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
            print(f"ERROR: retrieving destinations for plan ID {plan_id} - {e}")
            return []

    @staticmethod
    async def add_destination_to_plan(db: AsyncSession, plan_id: int, data: PlanDestinationCreate):
        try:
            new_plan_dest = PlanDestination(
                plan_id=plan_id,
                destination_id=data.destination_id,
                type=data.destination_type,
                visit_date=data.visit_date,
                note=data.note
            )
            db.add(new_plan_dest)
            await db.commit()
            await db.refresh(new_plan_dest)
            return new_plan_dest
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: adding destination {data.destination_id} to plan {plan_id} - {e}")
            return None
        
    @staticmethod
    async def update_plan_destination(db: AsyncSession, destination_id: str, updated_data: PlanDestinationUpdate):
        try:
            result = await db.execute(
                select(PlanDestination).where(PlanDestination.destination_id == destination_id)
            )
            plan_dest = result.scalar_one_or_none()
            if not plan_dest:
                print(f"WARNING: WARNING: Destination ID {destination_id} not found")
                return None

            if updated_data.visit_date is not None:
                plan_dest.visit_date = updated_data.visit_date
            if updated_data.note is not None:
                plan_dest.note = updated_data.note

            db.add(plan_dest)
            await db.commit()
            await db.refresh(plan_dest)
            return plan_dest
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: updating destination ID {destination_id} - {e}")
            return None

    @staticmethod
    async def remove_destination_from_plan(db: AsyncSession, destination_id: str):
        try:
            result = await db.execute(
                select(PlanDestination).where(PlanDestination.destination_id == destination_id)
            )
            plan_dest = result.scalar_one_or_none()
            if not plan_dest:
                print(f"WARNING: Destination ID {destination_id} not found")
                return False

            await db.delete(plan_dest)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: removing destination ID {destination_id} - {e}")
            return False
    
    @staticmethod
    async def add_user_plan(db: AsyncSession, user_id: int, plan_id: int):
        try:
            new_user_plan = UserPlan(
                user_id=user_id,
                plan_id=plan_id
            )
            db.add(new_user_plan)
            await db.commit()
            await db.refresh(new_user_plan)
            return new_user_plan
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: adding user plan for user ID {user_id} and plan ID {plan_id} - {e}")
            return None
        
    @staticmethod
    async def get_user_plans(db: AsyncSession, plan_id: int):
        try:
            result = await db.execute(
                select(UserPlan).where(UserPlan.plan_id == plan_id)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: retrieving user plans for plan ID {plan_id} - {e}")
            return []
    
    @staticmethod
    async def remove_user_plan(db: AsyncSession, user_id:int, plan_id:int):
        try:
            result = await db.execute(
                select(UserPlan).where(
                    UserPlan.user_id == user_id,
                    UserPlan.plan_id == plan_id
                )
            )
            user_plan = result.scalar_one_or_none()
            if not user_plan:
                print(f"WARNING: WARNING: UserPlan for user ID {user_id} and plan ID {plan_id} not found")
                return False

            await db.delete(user_plan)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: removing user plan for user ID {user_id} and plan ID {plan_id} - {e}")
            return False