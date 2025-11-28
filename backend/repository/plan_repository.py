from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from models.plan import *
from schemas.plan_schema import *

class PlanRepository:
    @staticmethod
    async def is_plan_owner(db: AsyncSession, user_id: int, plan_id: int) -> bool:
        try:
            result = await db.execute(
                select(PlanMember).where(
                    PlanMember.plan_id == plan_id, 
                    PlanMember.user_id == user_id, 
                    PlanMember.role == PlanRole.owner
                )
            )
            plan = result.scalar_one_or_none()
            return plan is not None
        except SQLAlchemyError as e:
            print(f"ERROR: checking plan ownership for user ID {user_id} and plan ID {plan_id} - {e}")
            return False
        
    @staticmethod
    async def is_member(db: AsyncSession, user_id: int, plan_id: int) -> bool:
        try:
            result = await db.execute(
                select(PlanMember).where(
                    PlanMember.user_id == user_id,
                    PlanMember.plan_id == plan_id,
                )
            )
            membership = result.scalar_one_or_none()
            return membership is not None
        except SQLAlchemyError as e:
            print(f"ERROR: checking membership for user ID {user_id} and plan ID {plan_id} - {e}")
            return False
    
    @staticmethod
    async def get_plan_by_user_id(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(select(Plan).join(PlanMember).where(PlanMember.user_id == user_id))
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
    async def create_plan(db: AsyncSession, plan_data: PlanCreate):
        try:
            new_plan = Plan(
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
        try:
            result = await db.execute(
                select(PlanDestination).where(PlanDestination.plan_id == plan_id)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: retrieving destinations for plan ID {plan_id} - {e}")
            return []

    @staticmethod
    async def get_next_order_in_day(db: AsyncSession, plan_id: int, visit_date) -> int:
        try:
            result = await db.execute(
                select(func.coalesce(func.max(PlanDestination.order_in_day), 0))
                .where(
                    PlanDestination.plan_id == plan_id,
                    PlanDestination.visit_date == visit_date
                )
            )
            max_order = result.scalar()
            return max_order + 1
        except SQLAlchemyError as e:
            print(f"ERROR: getting next order_in_day for plan {plan_id} and date {visit_date} - {e}")
            return 1

    @staticmethod
    async def add_destination_to_plan(db: AsyncSession, plan_id: int, data: PlanDestinationCreate):
        try:
            next_order = await PlanRepository.get_next_order_in_day(db, plan_id, data.visit_date)
            
            new_plan_dest = PlanDestination(
                plan_id=plan_id,
                destination_id=data.destination_id,
                type=data.destination_type,
                visit_date=data.visit_date,
                order_in_day=next_order,
                url=data.url,
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
    async def update_plan_destination(db: AsyncSession, plan_destination_id: int, updated_data: PlanDestinationUpdate):
        try:
            result = await db.execute(
                select(PlanDestination).where(
                    PlanDestination.id == plan_destination_id
                )
            )
            plan_dest = result.scalar_one_or_none()
            if not plan_dest:
                print(f"WARNING: Plan destination ID {plan_destination_id} not found")
                return None

            if updated_data.visit_date is not None and updated_data.visit_date != plan_dest.visit_date:
                new_order = await PlanRepository.get_next_order_in_day(db, plan_dest.plan_id, updated_data.visit_date)
                plan_dest.visit_date = updated_data.visit_date
                plan_dest.order_in_day = new_order
            
            if updated_data.note is not None:
                plan_dest.note = updated_data.note
            if updated_data.estimated_cost is not None:
                plan_dest.estimated_cost = updated_data.estimated_cost
            if updated_data.url is not None:
                plan_dest.url = updated_data.url
                
            db.add(plan_dest)
            await db.commit()
            await db.refresh(plan_dest)
            return plan_dest
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: updating plan destination ID {plan_destination_id} - {e}")
            return None

    @staticmethod
    async def reorder_destinations_after_delete(db: AsyncSession, plan_id: int, visit_date, deleted_order: int):
        """Cập nhật lại order_in_day cho các destination sau khi xóa một item"""
        try:
            result = await db.execute(
                select(PlanDestination)
                .where(
                    PlanDestination.plan_id == plan_id,
                    PlanDestination.visit_date == visit_date,
                    PlanDestination.order_in_day > deleted_order
                )
                .order_by(PlanDestination.order_in_day)
            )
            destinations = result.scalars().all()
            for dest in destinations:
                dest.order_in_day -= 1
                db.add(dest)
        except SQLAlchemyError as e:
            print(f"ERROR: reordering destinations for plan {plan_id} and date {visit_date} - {e}")

    @staticmethod
    async def remove_destination_from_plan(db: AsyncSession, plan_destination_id: int):
        try:
            result = await db.execute(
                select(PlanDestination).where(
                    PlanDestination.id == plan_destination_id
                )
            )
            plan_dest = result.scalar_one_or_none()
            if not plan_dest:
                print(f"WARNING: Plan destination ID {plan_destination_id} not found")
                return False

            # Lưu thông tin để reorder sau khi xóa
            plan_id = plan_dest.plan_id
            visit_date = plan_dest.visit_date
            deleted_order = plan_dest.order_in_day

            await db.delete(plan_dest)
            
            # Reorder các destination còn lại
            await PlanRepository.reorder_destinations_after_delete(db, plan_id, visit_date, deleted_order)
            
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: removing plan destination ID {plan_destination_id} - {e}")
            return False
    
    @staticmethod
    async def add_plan_member(db: AsyncSession, plan_id: int, data: PlanMemberCreate):
        try:
            new_plan_member = PlanMember(
                user_id=data.user_id,
                plan_id=plan_id,
                role=data.role
            )
            db.add(new_plan_member)
            await db.commit()
            await db.refresh(new_plan_member)
            return new_plan_member
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: adding plan member for user ID {data.user_id} and plan ID {plan_id} - {e}")
            return None
        
    @staticmethod
    async def get_plan_members(db: AsyncSession, plan_id: int):
        try:
            result = await db.execute(
                select(PlanMember).where(PlanMember.plan_id == plan_id)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: retrieving user plans for plan ID {plan_id} - {e}")
            return []
    
    @staticmethod
    async def remove_plan_member(db: AsyncSession, plan_id: int, member_id: int):
        try:
            result = await db.execute(
                select(PlanMember).where(
                    PlanMember.user_id == member_id,
                    PlanMember.plan_id == plan_id
                )
            )
            user_plan = result.scalar_one_or_none()
            if not user_plan:
                print(f"WARNING: WARNING: UserPlan for user ID {member_id} and plan ID {plan_id} not found")
                return False

            await db.delete(user_plan)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: removing user plan for user ID {member_id} and plan ID {plan_id} - {e}")
            return False
    
    @staticmethod
    async def get_all_plans(db: AsyncSession, skip: int = 0, limit: int = 100):
        try:
            result = await db.execute(
                select(Plan)
                .order_by(Plan.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: retrieving all plans - {e}")
            return []
    
    @staticmethod
    async def get_plan_destination_by_id(db: AsyncSession, plan_id: int, destination_id: str):
        try:
            result = await db.execute(
                select(PlanDestination).where(
                    PlanDestination.plan_id == plan_id,
                    PlanDestination.destination_id == destination_id
                )
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"ERROR: retrieving destination {destination_id} in plan {plan_id} - {e}")
            return None
    
    @staticmethod
    async def update_plan_member_role(db: AsyncSession, plan_id: int, user_id: int, new_role: PlanRole):
        try:
            result = await db.execute(
                select(PlanMember).where(
                    PlanMember.plan_id == plan_id,
                    PlanMember.user_id == user_id
                )
            )
            member = result.scalar_one_or_none()
            if not member:
                print(f"WARNING: Member {user_id} not found in plan {plan_id}")
                return None
            
            member.role = new_role
            db.add(member)
            await db.commit()
            await db.refresh(member)
            return member
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: updating role for user {user_id} in plan {plan_id} - {e}")
            return None