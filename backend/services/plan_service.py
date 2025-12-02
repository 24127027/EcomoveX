from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from repository.plan_repository import PlanRepository
from repository.room_repository import RoomRepository
from repository.message_repository import MessageRepository
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
    async def handle_intent(
        db: AsyncSession, user_id: int, room_id: int, user_text: str
    ) -> IntentHandlerResponse:
        try:
            rule_engine = RuleEngine()
            parse = rule_engine.classify(user_text)
            intent = parse.intent
            ent = parse.entities

            plans = await PlanRepository.get_plan_by_user_id(db, user_id)
            if not plans:
                return IntentHandlerResponse(ok=False, message="Không có plan nào để chỉnh sửa.")

            plan = plans[0]

            # -----------------------------
            # ADD intent
            # -----------------------------
            if intent == Intent.ADD:
                # FIX: đảm bảo user là member của plan trước khi add
                if not await PlanRepository.is_member(db, user_id, plan.id):
                    return IntentHandlerResponse(ok=False, message="Bạn không có quyền chỉnh sửa plan này.")

                destination_id = ent.get("destination_id")
                if not destination_id:
                    return IntentHandlerResponse(ok=False, message="Cần destination_id để thêm.")

                visit_date = ent.get("visit_date")
                order_in_day = ent.get("order_in_day", 1)
                note = ent.get("note") or ent.get("title") or "Hoạt động mới"
                dest_type = ent.get("type", "attraction")

                dest_data = PlanDestinationCreate(
                    destination_id=destination_id,
                    destination_type=dest_type,
                    order_in_day=order_in_day,
                    visit_date=visit_date,
                    note=note,
                )
                new_dest = await PlanRepository.add_destination_to_plan(db, plan.id, dest_data)
                if not new_dest:
                    return IntentHandlerResponse(ok=False, message="Không thể thêm destination.")

                # FIX: trả về full plan destinations để caller (ChatbotService) có dữ liệu cập nhật
                destinations = await PlanRepository.get_plan_destinations(db, plan.id)
                out = [
                    {
                        "id": dest.id,
                        "destination_id": dest.destination_id,
                        "type": dest.type,
                        "order_in_day": dest.order_in_day,
                        "visit_date": str(dest.visit_date) if dest.visit_date else None,
                        "note": dest.note,
                    }
                    for dest in destinations
                ]

                return IntentHandlerResponse(
                    ok=True,
                    action="add",
                    item={
                        "id": new_dest.id,
                        "destination_id": new_dest.destination_id,
                        "order_in_day": new_dest.order_in_day,
                        "note": new_dest.note,
                    },
                    data={"plan_id": plan.id, "destinations": out},
                )

            # -----------------------------
            # REMOVE intent
            # -----------------------------
            if intent == Intent.REMOVE:
                # dest_id ở đây phải là plan_destination_id (primary key của PlanDestination)
                dest_id = ent.get("item_id") or ent.get("destination_id")
                if dest_id:
                    # FIX: kiểm quyền: user phải là member để xóa
                    if not await PlanRepository.is_member(db, user_id, plan.id):
                        return IntentHandlerResponse(ok=False, message="Bạn không có quyền xóa destination trong plan này.")

                    ok = await PlanRepository.remove_destination_from_plan(db, dest_id)
                    if not ok:
                        return IntentHandlerResponse(ok=False, message="Không tìm thấy hoặc không xóa được destination.")
                    # FIX: trả về danh sách destinations sau khi xóa
                    destinations = await PlanRepository.get_plan_destinations(db, plan.id)
                    out = [
                        {
                            "id": dest.id,
                            "destination_id": dest.destination_id,
                            "type": dest.type,
                            "order_in_day": dest.order_in_day,
                            "visit_date": str(dest.visit_date) if dest.visit_date else None,
                            "note": dest.note,
                        }
                        for dest in destinations
                    ]
                    return IntentHandlerResponse(ok=True, action="remove", item_id=dest_id, data={"plan_id": plan.id, "destinations": out})

                return IntentHandlerResponse(ok=False, message="Cần id của destination để xóa.")

            # -----------------------------
            # MODIFY_TIME intent
            # -----------------------------
            if intent == Intent.MODIFY_TIME:
                dest_id = ent.get("item_id") or ent.get("destination_id")
                visit_date = ent.get("visit_date")
                order_in_day = ent.get("order_in_day")

                if not dest_id:
                    return IntentHandlerResponse(ok=False, message="Cần id của destination để đổi thời gian.")

                # FIX: chuẩn hóa update payload cho PlanDestination
                update_data = PlanDestinationUpdate(
                    visit_date=visit_date, order_in_day=order_in_day
                )

                # FIX: gọi đúng hàm update_plan_destination (đã thêm ở repository)
                updated = await PlanRepository.update_plan_destination(db, dest_id, update_data)
                if not updated:
                    return IntentHandlerResponse(ok=False, message="Không cập nhật được destination.")

                # FIX: trả về danh sách destinations sau cập nhật
                destinations = await PlanRepository.get_plan_destinations(db, plan.id)
                out = [
                    {
                        "id": dest.id,
                        "destination_id": dest.destination_id,
                        "type": dest.type,
                        "order_in_day": dest.order_in_day,
                        "visit_date": str(dest.visit_date) if dest.visit_date else None,
                        "note": dest.note,
                    }
                    for dest in destinations
                ]
                return IntentHandlerResponse(
                    ok=True,
                    action="modify_time",
                    item={
                        "id": updated.id,
                        "visit_date": str(updated.visit_date) if updated.visit_date else None,
                        "order_in_day": updated.order_in_day,
                    },
                    data={"plan_id": plan.id, "destinations": out},
                )

            # -----------------------------
            # CHANGE_BUDGET intent (giữ nguyên)
            # -----------------------------
            if intent == Intent.CHANGE_BUDGET:
                budget = ent.get("budget")
                update_data = PlanUpdate(budget_limit=budget)
                updated_plan = await PlanRepository.update_plan(db, plan.id, update_data)
                if not updated_plan:
                    return IntentHandlerResponse(ok=False, message="Không cập nhật được budget.")

                # FIX: lấy lại destinations để trả về data (consistent)
                destinations = await PlanRepository.get_plan_destinations(db, plan.id)
                out = [
                    {
                        "id": dest.id,
                        "destination_id": dest.destination_id,
                        "type": dest.type,
                        "order_in_day": dest.order_in_day,
                        "visit_date": str(dest.visit_date) if dest.visit_date else None,
                        "note": dest.note,
                    }
                    for dest in destinations
                ]

                return IntentHandlerResponse(ok=True, action="change_budget", budget=budget, data={"plan_id": plan.id, "destinations": out})

            # -----------------------------
            # VIEW_PLAN (giữ nguyên, trả plan)
            # -----------------------------
            if intent == Intent.VIEW_PLAN:
                destinations = await PlanRepository.get_plan_destinations(db, plan.id)
                out = [
                    {
                        "id": dest.id,
                        "destination_id": dest.destination_id,
                        "type": dest.type,
                        "order_in_day": dest.order_in_day,
                        "visit_date": str(dest.visit_date) if dest.visit_date else None,
                        "note": dest.note,
                    }
                    for dest in destinations
                ]
                return IntentHandlerResponse(
                    ok=True,
                    action="view_plan",
                    plan={
                        "id": plan.id,
                        "place_name": plan.place_name,
                        "destinations": out,
                    },
                )

            # -----------------------------
            # SUGGEST (giữ nguyên)
            # -----------------------------
            if intent == Intent.SUGGEST:
                suggestions = await RecommendationService.recommend_for_cluster_hybrid(db, user_id)
                return IntentHandlerResponse(ok=True, action="suggest", suggestions=suggestions)

            return IntentHandlerResponse(ok=False, message="Mình không hiểu yêu cầu, bạn nói lại được không?")

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error handling plan intent: {str(e)}",
            )

    @staticmethod
    async def join_plan(db: AsyncSession, user_id: int, plan_id: int) -> bool:
        try:
            # Check if plan exists
            plan = await PlanRepository.get_plan_by_id(db, plan_id)
            if not plan:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
            
            # Check if already member
            is_member = await PlanRepository.is_member(db, user_id, plan_id)
            if is_member:
                return True # Already joined
            
            result = await PlanRepository.add_member(db, plan_id, user_id)
            if not result:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to join plan")
            return True
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error joining plan: {e}")

    @staticmethod
    async def get_or_create_plan_chat_room(db: AsyncSession, user_id: int, plan_id: int) -> int:
        try:
            # 1. Check if user is member of plan
            if not await PlanRepository.is_member(db, user_id, plan_id):
                raise HTTPException(status_code=403, detail="User is not a member of this plan")

            room_name = f"PLAN_{plan_id}"
            
            # 2. Find room
            room = await RoomRepository.get_room_by_name(db, room_name)
            
            if room:
                # Ensure user is member
                if not await RoomRepository.is_member(db, user_id, room.id):
                    await RoomRepository.add_member(
                        db, room.id, RoomMemberCreate(user_id=user_id, role=MemberRole.member)
                    )
                return room.id
            
            # 3. Create room
            new_room = await RoomRepository.create_room(
                db, RoomCreate(name=room_name, room_type=RoomType.group)
            )
            if not new_room:
                raise HTTPException(status_code=500, detail="Failed to create chat room")
                
            # 4. Add user as admin
            await RoomRepository.add_member(
                db, new_room.id, RoomMemberCreate(user_id=user_id, role=MemberRole.admin)
            )
            
            # 5. Set Context
            await MessageRepository.save_room_context(
                db, RoomContextCreate(room_id=new_room.id, key="active_trip_id", value=plan_id)
            )
            
            return new_room.id

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting plan chat room: {e}",
            )

