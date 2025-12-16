from typing import List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.destination import Destination
from services.destination_service import DestinationService
from repository.plan_repository import PlanRepository
from repository.message_repository import MessageRepository
from repository.cluster_repository import ClusterRepository
from schemas.map_schema import *
from schemas.plan_schema import *
from schemas.route_schema import FindRoutesRequest, RouteCreate, RouteResponse, TransportMode
from schemas.room_schema import RoomCreate, RoomMemberCreate
from schemas.message_schema import RoomContextCreate, CommonMessageResponse
from schemas.route_schema import RouteType
from services.map_service import MapService
from services.route_service import RouteService
from services.room_service import RoomService
from repository.plan_repository import PlanDestination
from services.recommendation_service import RecommendationService
from utils.nlp.rule_engine import Intent, RuleEngine
from models.room import RoomType, MemberRole
from models.plan import PlanDestination, TimeSlot, DestinationType
from schemas.room_schema import AddMemberRequest


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

            # 3. Add Destinations - OPTIMIZED: First ensure all destinations exist, then add to plan
            import asyncio
            
            # Step 1: Ensure all destinations exist (handle duplicates)
            unique_place_ids = list(set(dest.destination_id for dest in plan_data.destinations))
            for place_id in unique_place_ids:
                try:
                    await PlanRepository.ensure_destination(db, place_id)
                except Exception as e:
                    print(f"Warning ensuring destination {place_id}: {e}")
            
            # Commit all destinations at once
            await db.commit()
            
            # Step 2: Add destinations to plan sequentially (fast since no API calls)
            saved_dest_ids = []
            for dest_data in plan_data.destinations:
                try:
                    saved_dest = await PlanRepository.add_destination_to_plan(db, new_plan.id, dest_data)
                    saved_dest_ids.append(saved_dest.id)
                except Exception as e:
                    print(f"Error adding destination {dest_data.destination_id} to plan: {e}")
            
            # 4. Create routes between consecutive destinations - OPTIMIZED: Parallel processing
            if len(saved_dest_ids) > 1:
                saved_destinations = await PlanRepository.get_plan_destinations(db, new_plan.id)
                
                async def create_route_for_pair(i):
                    origin = saved_destinations[i]
                    destination = saved_destinations[i + 1]
                    
                    try:
                        origin_coords = await MapService.get_coordinates(origin.destination_id)
                        destination_coords = await MapService.get_coordinates(destination.destination_id)
                        
                        # Validate coordinates before making route request
                        if not origin_coords or not destination_coords:
                            print(f"ERROR: Failed to get coordinates for route {i}")
                            return None
                                                
                        route = await RouteService.find_three_optimal_routes(FindRoutesRequest(
                            origin=origin_coords,
                            destination=destination_coords
                        ))
                        
                        if route:
                            selected_route = None
                            if RouteType.smart_combination in route.routes:
                                selected_route = route.routes[RouteType.smart_combination]
                            else:
                                selected_route = route.routes[RouteType.low_carbon]
                            
                            await PlanRepository.create_route(db, RouteCreate(
                                plan_id=new_plan.id,
                                origin_plan_destination_id=origin.id,
                                destination_plan_destination_id=destination.id,
                                distance_km=selected_route.distance,
                                carbon_emission_kg=selected_route.carbon,
                                mode=TransportMode.car
                            ))
                    except Exception as e:
                        print(f"Error creating route {i}: {e}")
                        return None
                
                # Process all routes in parallel
                await asyncio.gather(
                    *[create_route_for_pair(i) for i in range(len(saved_destinations) - 1)],
                    return_exceptions=True
                )

            saved_destinations = await PlanRepository.get_plan_destinations(db, new_plan.id)
            
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
            
            await PlanRepository.delete_all_plan_destination(db, plan_id)

            print(f"✅ UPDATING PLAN {plan_id}: Received {len(updated_data.destinations or [])} destinations")
            
            saved_dest_ids = []
            for dest_data in updated_data.destinations or []:
                try:
                    place_info = await MapService.get_location_details(
                        PlaceDetailsRequest(place_id=dest_data.destination_id),
                        db=db,
                        user_id=user_id
                    )
                    await PlanRepository.ensure_destination(db, place_info.place_id)
                    
                    if not dest_data.url and place_info.photos:
                        dest_data.url = place_info.photos[0].photo_url
                except Exception as e:
                    print(f"Warning syncing destination {dest_data.destination_id}: {e}")
                
                saved_dest = await PlanRepository.add_destination_to_plan(db, plan_id, dest_data)
                saved_dest_ids.append(saved_dest.id)
            
            if len(saved_dest_ids) > 1:
                saved_destinations = await PlanRepository.get_plan_destinations(db, plan_id)
                for i in range(len(saved_destinations) - 1):
                    origin = saved_destinations[i]
                    destination = saved_destinations[i + 1]
                    origin_coords = await MapService.get_coordinates(origin.destination_id)
                    destination_coords = await MapService.get_coordinates(destination.destination_id)
                    route = await RouteService.find_three_optimal_routes(FindRoutesRequest(
                        origin=origin_coords,
                        destination=destination_coords
                    ))
                    if route:
                        selected_route = None
                        if RouteType.smart_combination in route.routes:
                            selected_route = route.routes[RouteType.smart_combination]
                        else:
                            selected_route = route.routes[RouteType.low_carbon]
                        
                        await PlanRepository.create_route(db, RouteCreate(
                            plan_id=plan_id,
                            origin_plan_destination_id=origin.id,
                            destination_plan_destination_id=destination.id,
                            distance_km=selected_route.distance,
                            carbon_emission_kg=selected_route.carbon,
                            mode=TransportMode.car
                        ))

            saved_destinations = await PlanRepository.get_plan_destinations(db, updated_plan.id)
            
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
                    PlaceDetailsRequest(place_id=data.destination_id),
                    db=db,
                    user_id=user_id
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

            room = None
            try:
                room = await RoomService.get_room_by_plan_id(db, user_id, plan_id)
            except HTTPException as e:
                if e.status_code == status.HTTP_404_NOT_FOUND:
                    room_name = f"{plan.place_name} - Group Chat"
                    room = await RoomService.create_room(db, user_id, RoomCreate(
                        name=room_name,
                        member_ids=[],
                        avatar_blob_name=None,
                        plan_id=plan_id
                    ))
                    await RoomService.add_users_to_room(
                        db,
                        user_id,
                        room.id,
                        AddMemberRequest(data=[
                            RoomMemberCreate(user_id=user_id, role=MemberRole.owner)
                        ]),
                    )
                else:
                    raise

            duplicates = []
            members_to_add = []
            for member in data.ids:
                if await PlanService.is_member(db, member.user_id, plan_id):
                    duplicates.append(member.user_id)
                    continue
                await PlanService.add_plan_member(
                    db,
                    plan_id,
                    PlanMemberCreate(user_id=member.user_id, role=member.role),
                )
                # Collect members to add to room
                members_to_add.append(
                    RoomMemberCreate(user_id=member.user_id, role=MemberRole.member)
                )
            
            # Add all members to group room in one call
            if members_to_add and room:
                await RoomService.add_users_to_room(
                    db,
                    user_id,
                    room.id,
                    AddMemberRequest(data=members_to_add),
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
                origin_plan_destination_id=new_route.origin_place_id,
                destination_plan_destination_id=new_route.destination_place_id,
                distance_km=new_route.distance_km,
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
                    id=route.id,
                    plan_id=route.plan_id,
                    origin_plan_destination_id=route.origin_place_id,
                    destination_plan_destination_id=route.destination_place_id,
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
                id=route.id,
                plan_id=route.plan_id,
                origin_plan_destination_id=route.origin_place_id,
                destination_plan_destination_id=route.destination_place_id,
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
            
    @staticmethod
    async def update_route(
        db: AsyncSession,
        user_id: int,
        route_id: int,
        mode: TransportMode,
        carbon_emission_kg: float,
    ) -> bool:
        try:
            route = await PlanRepository.get_route_by_id(db, route_id)
            if not route:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Route with ID {route_id} not found",
                )
            
            is_member = await PlanRepository.is_member(db, user_id, route.plan_id)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User is not a member of the plan",
                )
            
            success = await PlanRepository.update_route(db, route_id, mode, carbon_emission_kg)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update route",
                )
            return success
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error updating route: {e}",
            )
            
    @staticmethod
    async def remove_place_by_name(db: AsyncSession, user_id: int, plan_id: int, text: str) -> PlanResponse:
        """Remove destinations from plan by name search"""
        try:
            # Check permission
            is_member = await PlanRepository.is_member(db, user_id, plan_id)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User is not a member of the plan",
                )

            # Get all destinations
            destinations = await PlanRepository.get_plan_destinations(db, plan_id)
            text_lower = text.lower()
            
            print(f"🔍 Searching for destination to remove: '{text}'")
            print(f"📋 Plan has {len(destinations)} destinations")

            # Find and remove matching destinations
            removed_count = 0
            for dest in destinations:
                # Try to get name from MapService
                try:
                    dest_info = await MapService.get_location_details(
                    PlaceDetailsRequest(place_id=dest.destination_id),
                    db=db,
                    user_id=user_id
                )
                    dest_name = dest_info.name if dest_info else None
                except Exception as e:
                    print(f"⚠️ Failed to get location details for {dest.destination_id}: {e}")
                    dest_name = None
                
                # Fallback to note field if MapService fails
                if not dest_name:
                    dest_name = dest.note
                
                print(f"🏷️ Destination {dest.id}: name='{dest_name}', note='{dest.note}'")
                
                # Check if text matches name or note
                if dest_name and text_lower in dest_name.lower():
                    print(f"✅ Match found! Removing destination {dest.id}")
                    await PlanRepository.remove_destination_from_plan(db, dest.id)
                    removed_count += 1
                elif dest.note and text_lower in dest.note.lower():
                    print(f"✅ Match found in note! Removing destination {dest.id}")
                    await PlanRepository.remove_destination_from_plan(db, dest.id)
                    removed_count += 1

            print(f"📊 Removed {removed_count} destination(s)")

            if removed_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No destination found matching '{text}'",
                )

            # Return updated plan
            return await PlanService.get_plan_by_id(db, user_id, plan_id)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error removing destination: {e}",
            )
    
    @staticmethod
    async def remove_place_by_id(db: AsyncSession, user_id: int, plan_id: int, plan_destination_id: int) -> PlanResponse:
        """Remove a specific destination from plan by its plan_destination ID"""
        try:
            # Check permission
            is_member = await PlanRepository.is_member(db, user_id, plan_id)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User is not a member of the plan",
                )

            # Remove the destination
            success = await PlanRepository.remove_destination_from_plan(db, plan_destination_id)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Destination with ID {plan_destination_id} not found in plan",
                )

            # Return updated plan
            return await PlanService.get_plan_by_id(db, user_id, plan_id)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error removing destination: {e}",
            )
    
    @staticmethod
    async def update_budget(db: AsyncSession, user_id: int, plan_id: int, budget: float) -> PlanResponse:
        """Update plan budget limit"""
        try:
            # Check permission
            is_member = await PlanRepository.is_member(db, user_id, plan_id)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User is not a member of the plan",
                )

            # Update budget
            updated = await PlanRepository.update_plan(
                db, plan_id, PlanUpdate(budget_limit=budget)
            )

            if not updated:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update budget",
                )

            # Return updated plan
            return await PlanService.get_plan_by_id(db, user_id, plan_id)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating budget: {e}",
            )

    @staticmethod
    async def add_place_by_text(db: AsyncSession, user_id: int, plan_id: int, text: str) -> PlanDestinationResponse:
        """Add a destination to plan by searching for it by text"""
        try:
            # Check permission
            is_member = await PlanRepository.is_member(db, user_id, plan_id)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User is not a member of the plan",
                )

            # Search for place
            data = TextSearchRequest(query=text)
            resp = await MapService.text_search_place(db, data, user_id)

            if not resp.results:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No results found for '{text}'",
                )

            # Pick first result
            first = resp.results[0]

            # Get place details including photo
            try:
                place_details = await MapService.get_location_details(
                    PlaceDetailsRequest(place_id=first.place_id),
                    db=db,
                    user_id=user_id
                )
                photo_url = place_details.photos[0].photo_url if place_details.photos else None
            except Exception:
                photo_url = None

            # Ensure destination exists in DB
            await PlanRepository.ensure_destination(db, first.place_id)

            # Get plan to determine defaults
            from datetime import date
            plan = await PlanRepository.get_plan_by_id(db, plan_id)
            
            # Set defaults: use plan start date if available, otherwise today
            default_date = plan.start_date if plan and plan.start_date else date.today()
            
            # Get existing destinations to determine order
            existing_destinations = await PlanRepository.get_plan_destinations(db, plan_id)
            next_order = len(existing_destinations) + 1

            # Add to plan with all required fields
            plan_dest_data = PlanDestinationCreate(
                destination_id=first.place_id,
                destination_type=DestinationType.attraction,
                order_in_day=next_order,
                visit_date=default_date,
                time_slot=TimeSlot.morning,  # Default to morning
                url=photo_url,
            )

            plan_dest = await PlanRepository.add_destination_to_plan(db, plan_id, plan_dest_data)

            return PlanDestinationResponse(
                id=plan_dest.id,
                destination_id=plan_dest.destination_id,
                type=plan_dest.type,
                visit_date=plan_dest.visit_date,
                estimated_cost=plan_dest.estimated_cost,
                url=plan_dest.url,
                note=plan_dest.note,
                order_in_day=plan_dest.order_in_day or 0,
                time_slot=plan_dest.time_slot,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error adding place: {e}",
            )