from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.plan import (
    Plan,
    PlanDestination,
    PlanMember,
    PlanRole,
    Route
)
from schemas.plan_schema import (
    PlanCreate,
    PlanDestinationCreate,
    PlanDestinationUpdate,
    PlanMemberCreate,
    PlanUpdate,
)
from schemas.route_schema import RouteCreate, TransportMode
from models.destination import Destination




class PlanRepository:
    @staticmethod
    async def is_plan_owner(db: AsyncSession, user_id: int, plan_id: int) -> bool:
        try:
            result = await db.execute(
                select(PlanMember).where(
                    PlanMember.plan_id == plan_id,
                    PlanMember.user_id == user_id,
                    PlanMember.role == PlanRole.owner,
                )
            )
            plan = result.scalar_one_or_none()
            return plan is not None
        except SQLAlchemyError as e:
            print(
                f"ERROR: checking plan ownership for user ID {user_id} and plan ID {plan_id} - {e}"
            )
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
            print(
                f"ERROR: checking membership for user ID {user_id} and plan ID {plan_id} - {e}"
            )
            return False

    @staticmethod
    async def get_plan_by_user_id(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(
                select(Plan)
                .join(PlanMember)
                .where(PlanMember.user_id == user_id)
                .options(selectinload(Plan.members))
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: retrieving plans for user ID {user_id} - {e}")
            return []

    @staticmethod
    async def get_plan_by_id(db: AsyncSession, plan_id: int):
        try:
            result = await db.execute(
                select(Plan)
                .options(selectinload(Plan.members))
                .where(Plan.id == plan_id)
            )
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
                budget_limit=plan_data.budget_limit,
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
    async def add_destination_to_plan(
        db: AsyncSession, plan_id: int, data: PlanDestinationCreate
    ):
        try:
            new_plan_dest = PlanDestination(
                plan_id=plan_id,
                destination_id=data.destination_id,
                type=data.destination_type,
                order_in_day=data.order_in_day,
                visit_date=data.visit_date,
                estimated_cost=data.estimated_cost,
                url=data.url,
                note=data.note,
                time_slot=data.time_slot,
            )
            db.add(new_plan_dest)
            await db.commit()
            await db.refresh(new_plan_dest)
            return new_plan_dest
        except SQLAlchemyError as e:
            await db.rollback()
            print(
                f"ERROR: adding destination {data.destination_id} to plan {plan_id} - {e}"
            )
            return None

    @staticmethod
    async def update_plan_destination(
        db: AsyncSession,
        plan_id: int,
        destination_id: str,
        updated_data: PlanDestinationUpdate,
    ):
        try:
            result = await db.execute(
                select(PlanDestination).where(
                    PlanDestination.plan_id == plan_id,
                    PlanDestination.destination_id == destination_id,
                )
            )
            plan_dest = result.scalar_one_or_none()
            if not plan_dest:
                print(
                    f"WARNING: WARNING: Destination {destination_id} in plan ID {plan_id} not found"
                )
                return None

            if updated_data.visit_date is not None:
                plan_dest.visit_date = updated_data.visit_date
            if updated_data.order_in_day is not None:
                plan_dest.order_in_day = updated_data.order_in_day
            if updated_data.estimated_cost is not None:
                plan_dest.estimated_cost = updated_data.estimated_cost
            if updated_data.url is not None:
                plan_dest.url = updated_data.url
            if updated_data.note is not None:
                plan_dest.note = updated_data.note

            db.add(plan_dest)
            await db.commit()
            await db.refresh(plan_dest)
            return plan_dest
        except SQLAlchemyError as e:
            await db.rollback()
            print(
                f"ERROR: updating destination {destination_id} in plan ID {plan_id} - {e}"
            )
            return None

    @staticmethod
    async def delete_all_plan_destination(db: AsyncSession, plan_id: int):
        try:
            result = await db.execute(
                select(PlanDestination).where(PlanDestination.plan_id == plan_id)
            )
            plan_destinations = result.scalars().all()
            for dest in plan_destinations:
                await db.delete(dest)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: deleting destinations for plan ID {plan_id} - {e}")
            return False

    @staticmethod
    async def add_plan_member(db: AsyncSession, plan_id: int, data: PlanMemberCreate):
        try:
            new_plan_member = PlanMember(
                user_id=data.user_id, plan_id=plan_id, role=data.role
            )
            db.add(new_plan_member)
            await db.commit()
            await db.refresh(new_plan_member)
            return new_plan_member
        except SQLAlchemyError as e:
            await db.rollback()
            print(
                f"ERROR: adding plan member for user ID {data.user_id} and plan ID {plan_id} - {e}"
            )
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
                    PlanMember.user_id == member_id, PlanMember.plan_id == plan_id
                )
            )
            user_plan = result.scalar_one_or_none()
            if not user_plan:
                print(
                    f"WARNING: WARNING: UserPlan for user ID {member_id} and plan ID {plan_id} not found"
                )
                return False

            await db.delete(user_plan)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(
                f"ERROR: removing user plan for user ID {member_id} and plan ID {plan_id} - {e}"
            )
            return False

    @staticmethod
    async def get_all_plans(db: AsyncSession, skip: int = 0, limit: int = 100):
        try:
            result = await db.execute(
                select(Plan).order_by(Plan.created_at.desc()).offset(skip).limit(limit)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: retrieving all plans - {e}")
            return []

    @staticmethod
    async def get_plan_destination_by_plan_and_dest_id(
        db: AsyncSession, plan_id: int, destination_id: str
    ):
        try:
            result = await db.execute(
                select(PlanDestination).where(
                    PlanDestination.plan_id == plan_id,
                    PlanDestination.destination_id == destination_id,
                )
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(
                f"ERROR: retrieving destination {destination_id} in plan {plan_id} - {e}"
            )
            return None

    @staticmethod
    async def get_plan_destination_by_id(db: AsyncSession, plan_destination_id: int):
        try:
            result = await db.execute(
                select(PlanDestination).where(PlanDestination.id == plan_destination_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"ERROR: retrieving plan destination ID {plan_destination_id} - {e}")
            return None

    @staticmethod
    async def update_plan_member_role(
        db: AsyncSession, plan_id: int, user_id: int, new_role: PlanRole
    ):
        try:
            result = await db.execute(
                select(PlanMember).where(
                    PlanMember.plan_id == plan_id, PlanMember.user_id == user_id
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

    @staticmethod
    async def remove_destination_from_plan(
        db: AsyncSession, plan_destination_id: int
    ) -> bool:
        try:
            result = await db.execute(
                select(PlanDestination).where(PlanDestination.id == plan_destination_id)
            )
            dest = result.scalar_one_or_none()
            if not dest:
                print(f"WARNING: PlanDestination ID {plan_destination_id} not found")
                return False

            await db.delete(dest)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: deleting plan destination ID {plan_destination_id} - {e}")
            return False

    @staticmethod
    async def ensure_destination(db: AsyncSession, place_id: str):
        """Check and create destination if it doesn't exist to avoid FK error"""
        try:
            # 1. Check if exists
            result = await db.execute(
                select(Destination).where(Destination.place_id == place_id)
            )
            existing = result.scalar_one_or_none()
            if existing:
                return existing

            # 2. Create new destination
            new_dest = Destination(place_id=place_id)
            db.add(new_dest)
            await db.flush()  # Use flush instead of commit to keep transaction open
            return new_dest
        except SQLAlchemyError as e:
            # If error (e.g., duplicate key from race condition), rollback and retry check
            await db.rollback()
            print(f"ERROR ensuring destination {place_id}: {e}")
            # Retry check in case another parallel task created it
            result = await db.execute(
                select(Destination).where(Destination.place_id == place_id)
            )
            existing = result.scalar_one_or_none()
            if existing:
                return existing
            return None

    @staticmethod
    async def create_route(db: AsyncSession, route_data: RouteCreate) -> Route:
        try:
            new_route = Route(
                plan_id=route_data.plan_id,
                origin_place_id=route_data.origin_plan_destination_id,
                destination_place_id=route_data.destination_plan_destination_id,
                distance_km=route_data.distance_km,
                carbon_emission_kg=route_data.carbon_emission_kg,
            )
            db.add(new_route)
            await db.commit()
            await db.refresh(new_route)
            return new_route
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: creating route - {e}")
            return None

    @staticmethod
    async def get_all_routes_by_plan_id(db: AsyncSession, plan_id: int) -> list[Route]:
        try:
            result = await db.execute(
                select(Route).where(Route.plan_id == plan_id)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: retrieving routes for plan ID {plan_id} - {e}")
            return []

    @staticmethod
    async def get_route_by_origin_and_destination(
        db: AsyncSession,
        plan_id: int,
        origin_plan_destination_id: int,
        destination_plan_destination_id: int
    ) -> Route | None:
        try:
            result = await db.execute(
                select(Route).where(
                    Route.plan_id == plan_id,
                    Route.origin_place_id == origin_plan_destination_id,
                    Route.destination_place_id == destination_plan_destination_id
                )
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"ERROR: retrieving route for plan ID {plan_id} from {origin_plan_destination_id} to {destination_plan_destination_id} - {e}")
            return None

    @staticmethod
    async def get_route_by_id(db: AsyncSession, route_id: int) -> Route:
        try:
            result = await db.execute(
                select(Route).where(Route.id == route_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"ERROR: retrieving route ID {route_id} - {e}")
            return None

    @staticmethod
    async def update_route(db: AsyncSession, route_id: int, mode: TransportMode, carbon_emission_kg: float) -> bool:
        try:
            result = await db.execute(
                select(Route).where(Route.id == route_id)
            )
            route = result.scalar_one_or_none()
            if not route:
                print(f"WARNING: Route ID {route_id} not found")
                return False

            route.mode = mode
            route.carbon_emission_kg = carbon_emission_kg

            db.add(route)
            await db.commit()
            await db.refresh(route)
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: updating route ID {route_id} - {e}")
            return False
