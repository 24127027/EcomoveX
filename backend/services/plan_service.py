from typing import List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.plan import PlanRole, DestinationType, TimeSlot
from repository.plan_repository import PlanRepository
from repository.room_repository import RoomRepository
from repository.message_repository import MessageRepository
from repository.cluster_repository import ClusterRepository
from schemas.map_schema import *
from schemas.plan_schema import *
from schemas.route_schema import RouteCreate, RouteResponse
from schemas.room_schema import RoomCreate, RoomMemberCreate
from schemas.message_schema import RoomContextCreate, CommonMessageResponse
from services.map_service import MapService
from services.route_service import RouteService
from repository.plan_repository import PlanDestination


class PlanService:
    @staticmethod
    async def is_plan_owner(db: AsyncSession, user_id: int, plan_id: int) -> bool:
        try:
            return await PlanRepository.is_plan_owner(db, user_id, plan_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error checking plan ownership: {e}",
            )

    @staticmethod
    async def is_member(db: AsyncSession, user_id: int, plan_id: int) -> bool:
        try:
            return await PlanRepository.is_member(db, user_id, plan_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error checking plan membership: {e}",
            )

    @staticmethod
    async def get_plans_by_user(db: AsyncSession, user_id: int) -> AllPlansResponse:
        try:
            plans = await PlanRepository.get_plan_by_user_id(db, user_id)
            if plans is None:
                return AllPlansResponse(plans=[])
                
            return AllPlansResponse(
                plans=[
                    PlanResponseBasic(
                        id=plan.id,
                        place_name=plan.place_name,
                        budget_limit=plan.budget_limit,
                    )
                    for plan in plans
                ]
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving plans for user ID {user_id}: {e}",
            )
            
    @staticmethod
    async def get_plan_by_id(db: AsyncSession,user_id: int, plan_id: int) -> PlanResponse:
        try:
            is_member = await PlanRepository.is_member(db, user_id, plan_id)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User is not a member of the plan",
                )
            plan = await PlanRepository.get_plan_by_id(db, plan_id)
            if not plan:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Plan with ID {plan_id} not found",
                )
            
            destinations = await PlanRepository.get_plan_destinations(db, plan.id)
            dest_infos = [
                PlanDestinationResponse(
                    id=dest.id,
                    destination_id=dest.destination_id,
                    type=dest.type,             
                    visit_date=dest.visit_date,
                    time_slot=dest.time_slot,
                    estimated_cost=dest.estimated_cost,
                    url=dest.url,
                    note=dest.note,
                    order_in_day=dest.order_in_day or 0,
                )
                for dest in destinations
            ]
            
            # Find owner
            owner_id = next((m.user_id for m in plan.members if m.role == PlanRole.owner), None)
            
            return PlanResponse(
                id=plan.id,
                user_id=owner_id,
                place_name=plan.place_name,
                start_date=plan.start_date,
                end_date=plan.end_date,
                budget_limit=plan.budget_limit,
                destinations=dest_infos,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving plan ID {plan_id}: {e}",
            )

    @staticmethod
    async def create_plan(
        db: AsyncSession, user_id: int, plan_data: PlanCreate
    ) -> PlanResponse:
        try:
            # 1. Tạo Plan
            new_plan = await PlanRepository.create_plan(db, plan_data)
            if not new_plan:
                raise HTTPException(status_code=500, detail="Failed to create plan")

            # 2. Add Owner
            await PlanRepository.add_plan_member(
                db, new_plan.id, PlanMemberCreate(user_id=user_id, role=PlanRole.owner)
            )

            # 3. Add Destinations (CÓ GỌI MAP SERVICE ĐỂ FIX LỖI FK)
            for dest_data in plan_data.destinations:
                try:
                    # Gọi MapService lấy thông tin để tạo Destination trong DB trước
                    place_info = await MapService.get_location_details(
                        PlaceDetailsRequest(place_id=dest_data.destination_id)
                    )
                    await PlanRepository.ensure_destination(db, place_info.place_id)

                    # Update URL ảnh nếu thiếu
                    if place_info.photos:
                        dest_data.url = place_info.photos[0].photo_url
                    
                    # Sau đó mới thêm vào Plan
                    await PlanRepository.add_destination_to_plan(db, new_plan.id, dest_data)
                    
                except Exception as e:
                    print(
                        f"❌ ERROR: Failed to add destination {dest_data.destination_id}: {e}"
                    )
                    print(f"   Skipping this destination and continuing with others...")
                    continue

            # 4. Return
            saved_destinations = await PlanRepository.get_plan_destinations(
                db, new_plan.id
            )
            
            list_route = []
            for i in range(len(saved_destinations) - 1):
                origin = saved_destinations[i].destination_id
                destination = saved_destinations[i + 1].destination_id
                routes = await RouteService.get_route_for_plan(origin, destination)
                list_route.extend(routes)
            
            return PlanResponse(
                id=new_plan.id,
                user_id=user_id,
                place_name=new_plan.place_name,
                start_date=new_plan.start_date,
                end_date=new_plan.end_date,
                budget_limit=new_plan.budget_limit,
                destinations=[
                    PlanDestinationResponse(
                        id=dest.id,
                        destination_id=dest.destination_id,
                        destination_type=dest.type,
                        type=dest.type,
                        visit_date=dest.visit_date,
                        estimated_cost=dest.estimated_cost,
                        url=dest.url,
                        note=dest.note,
                        order_in_day=dest.order_in_day or 0,
                        time_slot=dest.time_slot,
                    )
                    for dest in saved_destinations
                ],
                route=list_route,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating plan: {e}")

    @staticmethod
    async def update_plan(
        db: AsyncSession, user_id: int, plan_id: int, updated_data: PlanUpdate
    ):
        try:
            plans = await PlanRepository.get_plan_by_user_id(db, user_id)
            if not plans or not any(p.id == plan_id for p in plans):
                raise HTTPException(status_code=404, detail="Plan not found")

            updated_plan = await PlanRepository.update_plan(db, plan_id, updated_data)

            # ✅ DELETE OLD DESTINATIONS FIRST
            await PlanRepository.delete_all_plan_destination(db, plan_id)

            # ✅ ADD NEW DESTINATIONS
            for dest_data in updated_data.destinations:
                try:
                    place_info = await MapService.get_location_details(
                        PlaceDetailsRequest(place_id=dest_data.destination_id)
                    )
                    await PlanRepository.ensure_destination(db, place_info.place_id)
                    if place_info.photos:
                        dest_data.url = place_info.photos[0].photo_url
                except Exception as e:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error syncing destination {dest_data.destination_id}: {e}",
                    )

                await PlanRepository.add_destination_to_plan(db, plan_id, dest_data)

            saved_destinations = await PlanRepository.get_plan_destinations(
                db, updated_plan.id
            )

            list_route = []
            for i in range(len(saved_destinations) - 1):
                origin = saved_destinations[i].destination_id
                destination = saved_destinations[i + 1].destination_id
                routes = await RouteService.get_route_for_plan(origin, destination)
                list_route.extend(routes)

            return PlanResponse(
                id=updated_plan.id,
                user_id=user_id,
                place_name=updated_plan.place_name,
                start_date=updated_plan.start_date,
                end_date=updated_plan.end_date,
                budget_limit=updated_plan.budget_limit,
                destinations=[
                    PlanDestinationResponse(
                        id=dest.id,
                        destination_id=dest.destination_id,
                        destination_type=dest.type,
                        type=dest.type,
                        visit_date=dest.visit_date,
                        estimated_cost=dest.estimated_cost,
                        url=dest.url,
                        note=dest.note,
                        order_in_day=dest.order_in_day or 0,
                        time_slot=dest.time_slot,
                    )
                    for dest in saved_destinations
                ],
                route=list_route,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error: {e}")

    @staticmethod
    async def delete_plan(db: AsyncSession, user_id: int, plan_id: int):
        try:
            plan = await PlanRepository.get_plan_by_id(db, plan_id)
            if not plan:
                raise HTTPException(status_code=404, detail="Plan not found")

            is_owner = await PlanRepository.is_plan_owner(db, user_id, plan_id)
            if not is_owner:
                raise HTTPException(status_code=403, detail="Only owner can delete")

            success = await PlanRepository.delete_plan(db, plan_id)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to delete")

            return {"message": "Plan deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting: {e}")

    @staticmethod
    async def get_plan_destinations(
        db: AsyncSession, user_id: int, plan_id: int
    ) -> List[PlanDestinationResponse]:
        try:
            plan = await PlanRepository.get_plan_by_id(db, plan_id)
            if not plan:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Plan with ID {plan_id} not found",
                )

            is_member = await PlanRepository.is_member(db, user_id, plan_id)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User is not a member of the plan",
                )

            destinations = await PlanRepository.get_plan_destinations(db, plan_id)
            list_dest_responses = [
                PlanDestinationResponse(
                    id=dest.id,
                    destination_id=dest.destination_id,
                    destination_type=dest.type,
                    type=dest.type,
                    order_in_day=dest.order_in_day,
                    visit_date=dest.visit_date,
                    estimated_cost=dest.estimated_cost,
                    url=dest.url,
                    note=dest.note,
                    time_slot=dest.time_slot,
                )
                for dest in destinations
            ]
            return list_dest_responses
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving destinations for plan ID {plan_id}: {e}",
            )

    @staticmethod
    async def add_destination_to_plan(
        db: AsyncSession,
        user_id: int,
        plan_id: int,
        data: PlanDestinationCreate,
    ) -> PlanDestinationResponse:
        try:
            plan = await PlanRepository.get_plan_by_id(db, plan_id)
            if not plan:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Plan with ID {plan_id} not found",
                )

            is_member = await PlanRepository.is_member(db, user_id, plan_id)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only plan members can add destinations",
                )

            try:
                image = await MapService.get_location_details(
                    PlaceDetailsRequest(place_id=data.destination_id)
                )
                data.url = image.photos[0].photo_url if image.photos else None
            except Exception:
                data.url = None

            plan_dest = await PlanRepository.add_destination_to_plan(db, plan_id, data)

            if not plan_dest:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to add destination to plan",
                )

            return PlanDestinationResponse(
                id=plan_dest.id,
                destination_id=plan_dest.destination_id,
                destination_type=plan_dest.type,
                type=plan_dest.type,
                visit_date=plan_dest.visit_date,
                estimated_cost=plan_dest.estimated_cost,
                url=plan_dest.url,
                note=plan_dest.note,
                order_in_day=plan_dest.order_in_day,
                time_slot=plan_dest.time_slot,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error adding destination to plan: {e}",
            )

    @staticmethod
    async def delete_all_plan_destination(db: AsyncSession, plan_id: int) -> bool:
        try:
            success = await PlanRepository.delete_all_plan_destination(db, plan_id)
            return success
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error deleting all destinations for plan ID {plan_id}: {e}",
            )

    @staticmethod
    async def get_plan_members(db: AsyncSession, plan_id: int) -> PlanMemberResponse:
        try:
            plan = await PlanRepository.get_plan_by_id(db, plan_id)
            if not plan:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Plan with ID {plan_id} not found",
                )
            user_plans = await PlanRepository.get_plan_members(db, plan_id)
            return PlanMemberResponse(
                plan_id=plan_id,
                members=[
                    PlanMemberDetailResponse(
                        user_id=member.user_id,
                        plan_id=plan_id,
                        role=member.role,
                        joined_at=member.joined_at,
                    )
                    for member in user_plans
                ],
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving users for plan ID {plan_id}: {e}",
            )

    @staticmethod
    async def add_plan_member(
        db: AsyncSession, user_id: int, plan_id: int, data: MemberCreate
    ) -> PlanMemberResponse:
        try:
            plan = await PlanRepository.get_plan_by_id(db, plan_id)
            if not plan:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Plan with ID {plan_id} not found",
                )

            is_owner = await PlanRepository.is_plan_owner(db, user_id, plan_id)
            if not is_owner:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the owner can add members to the plan",
                )

            duplicates = []
            for member in data.ids:
                if await PlanService.is_member(db, member.user_id, plan_id):
                    duplicates.append(member.user_id)
                    continue
                await PlanRepository.add_plan_member(
                    db,
                    plan_id,
                    PlanMemberCreate(user_id=member.user_id, role=member.role),
                )
            users = await PlanRepository.get_plan_members(db, plan_id)
            return PlanMemberResponse(
                plan_id=plan_id,
                members=[
                    PlanMemberDetailResponse(
                        user_id=user.user_id,
                        plan_id=plan_id,
                        role=user.role,
                        joined_at=user.joined_at,
                    )
                    for user in users
                ],
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error associating user with plan: {e}",
            )

    @staticmethod
    async def remove_plan_member(
        db: AsyncSession, user_id: int, plan_id: int, data: MemberDelete
    ) -> PlanMemberResponse:
        try:
            plan = await PlanRepository.get_plan_by_id(db, plan_id)
            if not plan:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Plan with ID {plan_id} not found",
                )

            is_owner = await PlanRepository.is_plan_owner(db, user_id, plan_id)
            if not is_owner:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the owner can remove members from the plan",
                )

            ids_not_in_plan = []
            for member_id in data.ids:
                is_member_owner = await PlanRepository.is_plan_owner(
                    db, member_id, plan_id
                )
                if is_member_owner:
                    continue
                if not await PlanService.is_member(db, member_id, plan_id):
                    ids_not_in_plan.append(member_id)
                    continue
                await PlanRepository.remove_plan_member(db, plan_id, member_id)
            users = await PlanService.get_plan_members(db, plan_id)
            return PlanMemberResponse(
                plan_id=plan_id,
                members=[
                    PlanMemberDetailResponse(
                        user_id=user.user_id,
                        plan_id=plan_id,
                        role=user.role,
                        joined_at=user.joined_at,
                    )
                    for user in users.members
                ],
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error removing user from plan: {e}",
            )
            
   # hàm sắp xếp destinations dự theo đánh giá của plan_validator.py
    @staticmethod
    async def build_itinerary(destinations: List[PlanDestination]) -> List[PlanDestination]:
        """
        Sắp xếp lịch trình hợp lý dựa trên:
        - Ngày đi (visit_date)
        - Loại điểm đến (attraction > restaurant > accommodation > transport)
        - Sắp xếp tiếp theo khoảng cách tối ưu (RouteService)
        """

        if not destinations:
            return []

        # ------------------------------------------------------------
        # 1. Sắp xếp theo ngày
        # ------------------------------------------------------------
        destinations.sort(key=lambda d: d.visit_date)

        # ------------------------------------------------------------
        # 2. Group theo ngày
        # ------------------------------------------------------------
        result = []
        current_day = None
        group = []

        for d in destinations:
            if current_day is None:
                current_day = d.visit_date

            if d.visit_date != current_day:
                sorted_day = await PlanService._sort_single_day(group)
                result.extend(sorted_day)
                group = []
                current_day = d.visit_date

            group.append(d)

        # cuối cùng
        if group:
            sorted_day = await PlanService._sort_single_day(group)
            result.extend(sorted_day)

        return result

    @staticmethod
    async def _sort_single_day(destinations: List[PlanDestination]) -> List[PlanDestination]:
        """
        Sắp xếp các điểm đến trong cùng một ngày theo:
        - Loại điểm đến (ưu tiên: attraction > restaurant > accommodation > transport)
        - Time slot (morning < afternoon < evening)
        - Order in day
        """
        if not destinations:
            return []

        # Định nghĩa thứ tự ưu tiên cho loại điểm đến
        type_priority = {
            DestinationType.attraction: 1,
            DestinationType.restaurant: 2,
            DestinationType.accommodation: 3,
            DestinationType.transport: 4,
        }

        # Định nghĩa thứ tự ưu tiên cho time slot
        time_slot_priority = {
            TimeSlot.morning: 1,
            TimeSlot.afternoon: 2,
            TimeSlot.evening: 3,
        }

        def get_sort_key(dest: PlanDestination):
            dest_type = getattr(dest, 'type', None)
            time_slot = getattr(dest, 'time_slot', None)
            order = getattr(dest, 'order_in_day', 0) or 0

            type_order = type_priority.get(dest_type, 99)
            slot_order = time_slot_priority.get(time_slot, 99)

            return (slot_order, type_order, order)

        sorted_destinations = sorted(destinations, key=get_sort_key)
        return sorted_destinations

    @staticmethod
    async def create_route(
        db: AsyncSession, user_id: int, route_data: RouteCreate
    ) -> RouteResponse:
        """Create a new route between two destinations in a plan"""
        try:
            # Check if user is member of the plan
            is_member = await PlanRepository.is_member(db, user_id, route_data.plan_id)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only plan members can create routes",
                )

            # Verify both plan destinations exist and belong to the plan
            origin = await PlanRepository.get_plan_destination_by_id(
                db, route_data.origin_plan_destination_id
            )
            destination = await PlanRepository.get_plan_destination_by_id(
                db, route_data.destination_plan_destination_id
            )

            if not origin or origin.plan_id != route_data.plan_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Origin destination not found in plan {route_data.plan_id}",
                )

            if not destination or destination.plan_id != route_data.plan_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Destination not found in plan {route_data.plan_id}",
                )

            # Create the route
            new_route = await PlanRepository.create_route(db, route_data)
            if not new_route:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create route",
                )

            return RouteResponse(
                plan_id=new_route.plan_id,
                origin_place_id=new_route.origin_place_id,
                destination_place_id=new_route.destination_place_id,
                distance_km=new_route.distance_km,
                mode=new_route.mode,
                carbon_emission_kg=new_route.carbon_emission_kg,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error creating route: {e}",
            )

    @staticmethod
    async def get_all_routes_by_plan_id(
        db: AsyncSession, user_id: int, plan_id: int
    ) -> List[RouteResponse]:
        """Get all routes for a specific plan"""
        try:
            # Check if user is member
            is_member = await PlanRepository.is_member(db, user_id, plan_id)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User is not a member of the plan",
                )

            routes = await PlanRepository.get_all_routes_by_plan_id(db, plan_id)
            
            return [
                RouteResponse(
                    plan_id=route.plan_id,
                    origin_place_id=route.origin_place_id,
                    destination_place_id=route.destination_place_id,
                    distance_km=route.distance_km,
                    mode=route.mode,
                    carbon_emission_kg=route.carbon_emission_kg,
                )
                for route in routes
            ]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving routes: {e}",
            )

    @staticmethod
    async def get_route_by_origin_and_destination(
        db: AsyncSession,
        user_id: int,
        plan_id: int,
        origin_plan_destination_id: int,
        destination_plan_destination_id: int,
    ) -> RouteResponse:
        """Get a specific route between two destinations"""
        try:
            # Check if user is member
            is_member = await PlanRepository.is_member(db, user_id, plan_id)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User is not a member of the plan",
                )

            route = await PlanRepository.get_route_by_origin_and_destination(
                db, plan_id, origin_plan_destination_id, destination_plan_destination_id
            )
            if not route:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Route not found between destinations {origin_plan_destination_id} and {destination_plan_destination_id}",
                )

            return RouteResponse(
                plan_id=route.plan_id,
                origin_place_id=route.origin_place_id,
                destination_place_id=route.destination_place_id,
                distance_km=route.distance_km,
                mode=route.mode,
                carbon_emission_kg=route.carbon_emission_kg,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving route: {e}",
            )