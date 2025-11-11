from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, delete, and_
from models.route import *
from schemas.route_schema import *
from typing import Optional, List

class RouteRepository:
    @staticmethod
    async def create_route(
        db: AsyncSession,
        route_data: RouteCreate
    ) -> RouteResponse:
        try:
            new_route = Route(
                user_id=route_data.user_id,
                origin_id=route_data.origin_id,
                destination_id=route_data.destination_id,
                distance_km=route_data.distance_km,
                estimated_travel_time_min=route_data.estimated_travel_time_min,
                carbon_emission_kg=route_data.carbon_emission_kg,
                created_at=func.now()
            )
            db.add(new_route)
            await db.commit()
            await db.refresh(new_route)
            return RouteResponse.model_validate(new_route)
        except Exception as e:
            await db.rollback()
            print(f"ERROR: creating route: {route_data}, {e}")
            return None

    @staticmethod
    async def get_routes_by_user(
        db: AsyncSession,
        user_id: int,
        limit: Optional[int] = 10
    ) -> List[RouteResponse]:
        try:
            query = select(Route).where(Route.user_id == user_id)
            if limit:
                query = query.limit(limit)
            result = await db.execute(query)
            routes = result.scalars().all()
            return [RouteResponse.model_validate(route) for route in routes]
        except Exception as e:
            await db.rollback()
            print(f"ERROR: fetching routes for user {user_id} - {e}")
            return []

    @staticmethod
    async def get_route_by_id(
        db: AsyncSession,
        user_id: int,
        origin_id: int,
        destination_id: int
    ) -> Optional[RouteResponse]:
        try:
            query = select(Route).where(
                and_(
                    Route.user_id == user_id,
                    Route.origin_id == origin_id,
                    Route.destination_id == destination_id
                )
            )
            result = await db.execute(query)
            route = result.scalar_one_or_none()
            return RouteResponse.model_validate(route) if route else None
        except Exception as e:
            await db.rollback()
            print(f"ERROR: fetching route for user {user_id} from {origin_id} to {destination_id} - {e}")
            return None

    @staticmethod
    async def get_routes_by_origin(
        db: AsyncSession,
        origin_id: int,
        limit: Optional[int] = 10
    ) -> List[RouteResponse]:
        try:
            query = select(Route).where(Route.origin_id == origin_id)
            if limit:
                query = query.limit(limit)
            result = await db.execute(query)
            routes = result.scalars().all()
            return [RouteResponse.model_validate(route) for route in routes]
        except Exception as e:
            await db.rollback()
            print(f"ERROR: fetching routes from origin {origin_id} - {e}")
            return []

    @staticmethod
    async def get_routes_by_destination(
        db: AsyncSession,
        destination_id: int,
        limit: Optional[int] = 10
    ) -> List[RouteResponse]:
        """Get all routes going to a specific destination"""
        try:
            query = select(Route).where(Route.destination_id == destination_id)
            if limit:
                query = query.limit(limit)
            result = await db.execute(query)
            routes = result.scalars().all()
            return [RouteResponse.model_validate(route) for route in routes]
        except Exception as e:
            await db.rollback()
            print(f"ERROR: fetching routes from destination {destination_id} - {e}")
            return []

    @staticmethod
    async def update_route(
        db: AsyncSession,
        user_id: int,
        origin_id: int,
        destination_id: int,
        route_update: RouteUpdate
    ) -> Optional[RouteResponse]:
        try:
            query = select(Route).where(
                and_(
                    Route.user_id == user_id,
                    Route.origin_id == origin_id,
                    Route.destination_id == destination_id
                )
            )
            result = await db.execute(query)
            route = result.scalar_one_or_none()
            
            if not route:
                return None
            
            if route_update.distance_km is not None:
                route.distance_km = route_update.distance_km
            if route_update.estimated_travel_time_min is not None:
                route.estimated_travel_time_min = route_update.estimated_travel_time_min
            if route_update.carbon_emission_kg is not None:
                route.carbon_emission_kg = route_update.carbon_emission_kg
            
            await db.commit()
            await db.refresh(route)
            return RouteResponse.model_validate(route)
        except Exception as e:
            await db.rollback()
            print(f"ERROR: updating route for user {user_id} from {origin_id} to {destination_id} - {e}")
            return None

    @staticmethod
    async def delete_route(
        db: AsyncSession,
        user_id: int,
        origin_id: int,
        destination_id: int
    ) -> bool:
        try:
            query = delete(Route).where(
                and_(
                    Route.user_id == user_id,
                    Route.origin_id == origin_id,
                    Route.destination_id == destination_id
                )
            )
            result = await db.execute(query)
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            print(f"ERROR: deleting route for user {user_id} from {origin_id} to {destination_id} - {e}")
            return False
