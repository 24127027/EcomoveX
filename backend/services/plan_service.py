from typing import List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.plan import PlanRole, DestinationType, TimeSlot
from repository.plan_repository import PlanRepository
from repository.room_repository import RoomRepository
from repository.message_repository import MessageRepository
from schemas.map_schema import PlaceDetailsRequest
from schemas.plan_schema import (
    IntentHandlerResponse,
    MemberCreate,
    MemberDelete,
    PlanCreate,
    PlanDestinationCreate,
    PlanDestinationResponse,
    PlanDestinationUpdate,
    PlanMemberCreate,
    PlanMemberDetailResponse,
    PlanMemberResponse,
    PlanResponse,
    PlanUpdate,
)
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
                members = await PlanRepository.get_plan_members(db, plan.id)
                owner = next(
                    (m for m in members if m.role == PlanRole.owner), None
                )
                destinations = await PlanRepository.get_plan_destinations(db, plan.id)
                dest_infos = [
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
                    for dest in destinations
                ]
                plan_response = PlanResponse(
                    id=plan.id,
                    user_id=owner.user_id if owner else None,
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
                    await PlanRepository.ensure_destination(db, place_info)

                    # Update URL ảnh nếu thiếu
                    if place_info.photos:
                        dest_data.url = place_info.photos[0].photo_url
                except Exception as e:
                    print(
                        f"Warning syncing destination {dest_data.destination_id}: {e}"
                    )

                # Sau đó mới thêm vào Plan
                await PlanRepository.add_destination_to_plan(db, new_plan.id, dest_data)

            # 4. Return
            saved_destinations = await PlanRepository.get_plan_destinations(
                db, new_plan.id
            )
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

                await PlanRepository.add_destination_to_plan(
                    db, plan_id, dest_data
                )

            saved_destinations = await PlanRepository.get_plan_destinations(
                db, updated_plan.id
            )
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
                        estimated_cost=dest.estimated_cost,
                        url=dest.url,
                        note=dest.note,
                        order_in_day=dest.order_in_day or 0,
                        time_slot=dest.time_slot,
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
            return PlanMemberResponse(
                plan_id=plan_id,
                members=[
                    PlanMemberDetailResponse(
                        user_id=user.user_id,
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
            

    @staticmethod
    async def handle_intent(
        db: AsyncSession, user_id: int, room_id: int, user_text: str
    ) -> IntentHandlerResponse:
        try:
            rule_engine = RuleEngine()
            parse = rule_engine.classify(user_text)
            intent = parse.intent
            ent = parse.entities

            # Lấy plans của user
            plans = await PlanRepository.get_plan_by_user_id(db, user_id)
            if not plans:
                return IntentHandlerResponse(
                    ok=False, message="Không có plan nào để chỉnh sửa."
                )

            plan = plans[0]

            # Kiểm tra membership
            is_member = await PlanService.is_member(db, user_id, plan.id)
            if not is_member:
                return IntentHandlerResponse(
                    ok=False, message="Bạn không có quyền chỉnh sửa plan này."
                )

            # -----------------------------
            # ADD intent
            # -----------------------------
            if intent == Intent.ADD:
                destination_id = ent.get("destination_id")
                if not destination_id:
                    return IntentHandlerResponse(
                        ok=False, message="Cần destination_id để thêm địa điểm."
                    )

                visit_date = ent.get("visit_date")
                if not visit_date:
                    return IntentHandlerResponse(
                        ok=False, message="Cần ngày tham quan (visit_date)."
                    )

                order_in_day = ent.get("order_in_day", 1)
                note = ent.get("note") or ent.get("title") or ""
                dest_type = ent.get("type", DestinationType.attraction)
                estimated_cost = ent.get("estimated_cost")
                url = ent.get("url")
                time_slot = ent.get("time_slot", TimeSlot.morning)

                # Tạo destination data với đầy đủ fields
                dest_data = PlanDestinationCreate(
                    destination_id=destination_id,
                    destination_type=dest_type,
                    order_in_day=order_in_day,
                    visit_date=visit_date,
                    estimated_cost=estimated_cost,
                    url=url,
                    note=note,
                    time_slot=time_slot,
                )

                # Ensure destination exists để tránh FK error
                try:
                    await MapService.get_place_details(
                        PlaceDetailsRequest(place_id=destination_id)
                    )
                except Exception:
                    await PlanRepository.ensure_destination(db, destination_id)

                # Thêm destination vào plan
                new_dest = await PlanService.add_destination_to_plan(
                    db, user_id, plan.id, dest_data
                )

                # Lấy danh sách destinations để trả về
                destinations = await PlanService.get_plan_destinations(
                    db, user_id, plan.id
                )

                return IntentHandlerResponse(
                    ok=True,
                    action="add",
                    item={
                        "id": new_dest.id,
                        "destination_id": new_dest.destination_id,
                        "type": new_dest.type.value,
                        "order_in_day": new_dest.order_in_day,
                        "visit_date": str(new_dest.visit_date),
                        "estimated_cost": new_dest.estimated_cost,
                        "note": new_dest.note,
                        "time_slot": new_dest.time_slot.value,
                    },
                    plan={
                        "id": plan.id,
                        "place_name": plan.place_name,
                        "start_date": str(plan.start_date),
                        "end_date": str(plan.end_date),
                        "budget_limit": plan.budget_limit,
                        "destinations": [
                            {
                                "id": d.id,
                                "destination_id": d.destination_id,
                                "type": d.type.value,
                                "order_in_day": d.order_in_day,
                                "visit_date": str(d.visit_date),
                                "estimated_cost": d.estimated_cost,
                                "url": d.url,
                                "note": d.note,
                                "time_slot": d.time_slot.value,
                            }
                            for d in destinations
                        ],
                    },
                )

            # -----------------------------
            # REMOVE intent
            # -----------------------------
            if intent == Intent.REMOVE:
                # plan_destination_id (PlanDestination.id)
                plan_dest_id = ent.get("item_id")
                if not plan_dest_id:
                    return IntentHandlerResponse(
                        ok=False, message="Cần id của địa điểm trong plan để xóa."
                    )

                # Xóa destination khỏi plan
                success = await PlanRepository.remove_destination_from_plan(
                    db, plan_dest_id
                )
                if not success:
                    return IntentHandlerResponse(
                        ok=False,
                        message="Không tìm thấy hoặc không xóa được địa điểm.",
                    )

                # Lấy lại danh sách destinations sau khi xóa
                destinations = await PlanService.get_plan_destinations(
                    db, user_id, plan.id
                )

                return IntentHandlerResponse(
                    ok=True,
                    action="remove",
                    item_id=plan_dest_id,
                    plan={
                        "id": plan.id,
                        "place_name": plan.place_name,
                        "start_date": str(plan.start_date),
                        "end_date": str(plan.end_date),
                        "budget_limit": plan.budget_limit,
                        "destinations": [
                            {
                                "id": d.id,
                                "destination_id": d.destination_id,
                                "type": d.type.value,
                                "order_in_day": d.order_in_day,
                                "visit_date": str(d.visit_date),
                                "estimated_cost": d.estimated_cost,
                                "url": d.url,
                                "note": d.note,
                                "time_slot": d.time_slot.value,
                            }
                            for d in destinations
                        ],
                    },
                )

            # -----------------------------
            # MODIFY_TIME intent
            # -----------------------------
            if intent == Intent.MODIFY_TIME:
                # Cần destination_id (place_id) và plan_id để tìm PlanDestination
                destination_id = ent.get("destination_id")
                if not destination_id:
                    return IntentHandlerResponse(
                        ok=False, message="Cần destination_id để đổi thời gian."
                    )

                visit_date = ent.get("visit_date")
                order_in_day = ent.get("order_in_day")
                time_slot = ent.get("time_slot")

                # Tạo update data
                update_data = PlanDestinationUpdate(
                    visit_date=visit_date,
                    order_in_day=order_in_day,
                    time_slot=time_slot,
                )

                # Gọi repository update (nhận plan_id, destination_id, update_data)
                updated = await PlanRepository.update_plan_destination(
                    db, plan.id, destination_id, update_data
                )
                if not updated:
                    return IntentHandlerResponse(
                        ok=False, message="Không cập nhật được địa điểm."
                    )

                # Lấy lại destinations
                destinations = await PlanService.get_plan_destinations(
                    db, user_id, plan.id
                )

                return IntentHandlerResponse(
                    ok=True,
                    action="modify_time",
                    item={
                        "id": updated.id,
                        "destination_id": updated.destination_id,
                        "visit_date": str(updated.visit_date),
                        "order_in_day": updated.order_in_day,
                        "time_slot": updated.time_slot.value,
                    },
                    plan={
                        "id": plan.id,
                        "place_name": plan.place_name,
                        "start_date": str(plan.start_date),
                        "end_date": str(plan.end_date),
                        "budget_limit": plan.budget_limit,
                        "destinations": [
                            {
                                "id": d.id,
                                "destination_id": d.destination_id,
                                "type": d.type.value,
                                "order_in_day": d.order_in_day,
                                "visit_date": str(d.visit_date),
                                "estimated_cost": d.estimated_cost,
                                "url": d.url,
                                "note": d.note,
                                "time_slot": d.time_slot.value,
                            }
                            for d in destinations
                        ],
                    },
                )

            # -----------------------------
            # CHANGE_BUDGET intent
            # -----------------------------
            if intent == Intent.CHANGE_BUDGET:
                budget = ent.get("budget")
                if budget is None:
                    return IntentHandlerResponse(
                        ok=False, message="Cần giá trị budget mới."
                    )

                # Chỉ owner mới được đổi budget
                is_owner = await PlanService.is_plan_owner(db, user_id, plan.id)
                if not is_owner:
                    return IntentHandlerResponse(
                        ok=False, message="Chỉ chủ plan mới có thể thay đổi budget."
                    )

                update_data = PlanUpdate(budget_limit=budget)
                updated_plan = await PlanRepository.update_plan(
                    db, plan.id, update_data
                )
                if not updated_plan:
                    return IntentHandlerResponse(
                        ok=False, message="Không cập nhật được budget."
                    )

                # Lấy lại destinations
                destinations = await PlanService.get_plan_destinations(
                    db, user_id, plan.id
                )

                return IntentHandlerResponse(
                    ok=True,
                    action="change_budget",
                    budget=budget,
                    plan={
                        "id": updated_plan.id,
                        "place_name": updated_plan.place_name,
                        "start_date": str(updated_plan.start_date),
                        "end_date": str(updated_plan.end_date),
                        "budget_limit": updated_plan.budget_limit,
                        "destinations": [
                            {
                                "id": d.id,
                                "destination_id": d.destination_id,
                                "type": d.type.value,
                                "order_in_day": d.order_in_day,
                                "visit_date": str(d.visit_date),
                                "estimated_cost": d.estimated_cost,
                                "url": d.url,
                                "note": d.note,
                                "time_slot": d.time_slot.value,
                            }
                            for d in destinations
                        ],
                    },
                )

            # -----------------------------
            # VIEW_PLAN intent
            # -----------------------------
            if intent == Intent.VIEW_PLAN:
                destinations = await PlanService.get_plan_destinations(
                    db, user_id, plan.id
                )

                return IntentHandlerResponse(
                    ok=True,
                    action="view_plan",
                    plan={
                        "id": plan.id,
                        "place_name": plan.place_name,
                        "start_date": str(plan.start_date),
                        "end_date": str(plan.end_date),
                        "budget_limit": plan.budget_limit,
                        "destinations": [
                            {
                                "id": d.id,
                                "destination_id": d.destination_id,
                                "type": d.type.value,
                                "order_in_day": d.order_in_day,
                                "visit_date": str(d.visit_date),
                                "estimated_cost": d.estimated_cost,
                                "url": d.url,
                                "note": d.note,
                                "time_slot": d.time_slot.value,
                            }
                            for d in destinations
                        ],
                    },
                )

            # -----------------------------
            # SUGGEST intent
            # -----------------------------
            if intent == Intent.SUGGEST:
                suggestions = await RecommendationService.recommend_for_cluster_hybrid(
                    db, user_id
                )
                return IntentHandlerResponse(
                    ok=True, action="suggest", suggestions=suggestions
                )

            # Intent không được nhận diện
            return IntentHandlerResponse(
                ok=False, message="Mình không hiểu yêu cầu, bạn nói lại được không?"
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error handling plan intent: {str(e)}",
            )