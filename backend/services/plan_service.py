from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from repository.plan_repository import PlanRepository
from repository.room_repository import RoomRepository
from repository.message_repository import MessageRepository
from repository.cluster_repository import ClusterRepository
from schemas.map_schema import *
from schemas.plan_schema import *
from schemas.room_schema import RoomCreate, RoomMemberCreate
from schemas.message_schema import RoomContextCreate
from services.map_service import MapService
from services.recommendation_service import RecommendationService
from utils.nlp.rule_engine import Intent, RuleEngine
from models.room import RoomType, MemberRole


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
    async def get_plans_by_user(db: AsyncSession, user_id: int) -> List[PlanResponse]:
        try:
            plans = await PlanRepository.get_plan_by_user_id(db, user_id)
            if plans is None:
                return []
            list_plan_responses = []
            for plan in plans:
                destinations = await PlanRepository.get_plan_destinations(db, plan.id)
                dest_infos = [
                    PlanDestinationResponse(
                        id=dest.id,
                        destination_id=dest.destination_id,
                        destination_type=dest.type,
                        type=dest.type,             
                        visit_date=dest.visit_date,
                        time=dest.time.strftime("%H:%M") if dest.time else None,  # ✅ Chuyển time về format "HH:MM"
                        estimated_cost=dest.estimated_cost,
                        url=dest.url,
                        note=dest.note,
                        order_in_day=dest.order_in_day or 0,
                    )
                    for dest in destinations
                ]
                plan_response = PlanResponse(
                    id=plan.id,
                    user_id=next((m.user_id for m in plan.members if m.role == PlanRole.owner), user_id),
                    place_name=plan.place_name,
                    start_date=plan.start_date,
                    end_date=plan.end_date,
                    budget_limit=plan.budget_limit,
                    destinations=dest_infos,
                )
                list_plan_responses.append(plan_response)
            return list_plan_responses
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving plans for user ID {user_id}: {e}",
            )

    @staticmethod
    async def create_plan(db: AsyncSession, user_id: int, plan_data: PlanCreate) -> PlanResponse:
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
                    await PlanRepository.ensure_destination(db, place_info)
                    
                    # Update URL ảnh nếu thiếu
                    if not dest_data.url and place_info.photos:
                        dest_data.url = place_info.photos[0].photo_url
                except Exception as e:
                    print(f"Warning syncing destination {dest_data.destination_id}: {e}")
                
                # Sau đó mới thêm vào Plan
                await PlanRepository.add_destination_to_plan(db, new_plan.id, dest_data)

            # 4. Return
            saved_destinations = await PlanRepository.get_plan_destinations(db, new_plan.id)
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
                        time=dest.time.strftime("%H:%M") if dest.time else None,
                        estimated_cost=dest.estimated_cost,
                        url=dest.url,
                        note=dest.note,
                        order_in_day=dest.order_in_day or 0,
                    )
                    for dest in saved_destinations
                ],
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating plan: {e}")

    @staticmethod
    async def update_plan(db: AsyncSession, user_id: int, plan_id: int, updated_data: PlanUpdate):
        try:
            plans = await PlanRepository.get_plan_by_user_id(db, user_id)
            if not plans or not any(p.id == plan_id for p in plans):
                raise HTTPException(status_code=404, detail="Plan not found")

            updated_plan = await PlanRepository.update_plan(db, plan_id, updated_data)
            
            # ✅ DELETE OLD DESTINATIONS FIRST
            await PlanRepository.delete_all_plan_destination(db, plan_id)

            print(f"✅ UPDATING PLAN {plan_id}: Received {len(updated_data.destinations or [])} destinations")
            
            # ✅ ADD NEW DESTINATIONS
            for i, dest_data in enumerate(updated_data.destinations or []):
                try:
                    print(f"  📍 Adding destination {i+1}: {dest_data.destination_id}")
                    place_info = await MapService.get_location_details(
                        PlaceDetailsRequest(place_id=dest_data.destination_id)
                    )
                    await PlanRepository.ensure_destination(db, place_info)
                except Exception as e:
                    print(f"  ⚠️ Warning syncing destination {dest_data.destination_id}: {e}")
                    pass
                
                result = await PlanRepository.add_destination_to_plan(db, plan_id, dest_data)
                print(f"  ✅ Added destination {dest_data.destination_id} with ID {result.id if result else 'FAILED'}")

            saved_destinations = await PlanRepository.get_plan_destinations(db, updated_plan.id)
            print(f"✅ SAVED {len(saved_destinations)} destinations to plan {plan_id}")
            
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
                        time=dest.time.strftime("%H:%M") if dest.time else None,
                        estimated_cost=dest.estimated_cost,
                        url=dest.url,
                        note=dest.note,
                        order_in_day=dest.order_in_day or 0,
                    )
                    for dest in saved_destinations
                ],
            )
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
            list_ids = [user_plan.user_id for user_plan in user_plans]
            return PlanMemberResponse(plan_id=plan_id, ids=list_ids)
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
            for id in data.ids:
                if await PlanService.is_member(db, id, plan_id):
                    duplicates.append(id)
                    continue
                await PlanRepository.add_plan_member(
                    db,
                    plan_id,
                    PlanMemberCreate(user_id=id, role=PlanRole.member),
                )
            users = await PlanRepository.get_plan_members(db, plan_id)
            list_ids = [user.user_id for user in users]
            return PlanMemberResponse(plan_id=plan_id, ids=list_ids)
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
                is_member_owner = await PlanRepository.is_plan_owner(db, member_id, plan_id)
                if is_member_owner:
                    continue
                if not await PlanService.is_member(db, member_id, plan_id):
                    ids_not_in_plan.append(member_id)
                    continue
                await PlanRepository.remove_plan_member(db, plan_id, member_id)
            list = await PlanService.get_plan_members(db, plan_id)
            ids = list.ids
            return PlanMemberResponse(plan_id=plan_id, ids=ids)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error removing user from plan: {e}",
            )
            
   
    @staticmethod
    async def remove_destination(self, db, user_id, plan_id, plan_destination_id):
        if not await PlanRepository.is_member(db, user_id, plan_id):
            return {"ok": False, "message": "Bạn không có quyền xóa destination."}

        ok = await PlanRepository.remove_destination_from_plan(db, plan_destination_id)
        if not ok:
            return {"ok": False, "message": "Không thể xóa destination."}

        new_state = await self.get_plan_state(db, plan_id)
        return {"ok": True, "action": "remove", "item_id": plan_destination_id, "state": new_state}


    @staticmethod
    async def update_destination_time(self, db, user_id, plan_id, dest_id, update_data):
        if not await PlanRepository.is_member(db, user_id, plan_id):
            return {"ok": False, "message": "Không có quyền chỉnh sửa."}

        updated = await PlanRepository.update_plan_destination(db, dest_id, update_data)
        if not updated:
            return {"ok": False, "message": "Không cập nhật được destination."}

        new_state = await self.get_plan_state(db, plan_id)
        return {"ok": True, "action": "modify_time", "item": updated, "state": new_state}

    @staticmethod
    async def update_budget(self, db, user_id, plan_id, budget):
        updated = await PlanRepository.update_plan_destination(
            db, plan_id, PlanUpdate(budget_limit=budget)
        )

        if not updated:
            return {"ok": False, "message": "Không cập nhật budget."}

        new_state = await self.get_plan_state(db, plan_id)
        return {"ok": True, "action": "change_budget", "budget": budget, "state": new_state}

