from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from repository.destination_repository import DestinationRepository
from repository.plan_repository import PlanRepository
from schemas.plan_schema import *
from utils.nlp.rule_engine import RuleEngine, Intent
from services.recommendation_service import RecommendationService

class PlanService:
    @staticmethod
    async def is_plan_owner(db: AsyncSession, user_id: int, plan_id: int) -> bool:
        try:
            return await PlanRepository.is_plan_owner(db, user_id, plan_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error checking plan ownership: {e}"
            )
            
    @staticmethod
    async def is_member(db: AsyncSession, user_id: int, plan_id: int) -> bool:
        try:
            return await PlanRepository.is_member(db, user_id, plan_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error checking plan membership: {e}"
            )
    
    @staticmethod
    async def get_plans_by_user(db: AsyncSession, user_id: int) ->List[PlanResponse]:
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
                        type=dest.type,
                        visit_date=dest.visit_date,
                        time=dest.time,
                        estimated_cost=dest.estimated_cost,
                        note=dest.note
                    )
                    for dest in destinations
                ]
                plan_response = PlanResponse(
                    id=plan.id,
                    place_name=plan.place_name,
                    start_date=plan.start_date,
                    end_date=plan.end_date,
                    budget_limit=plan.budget_limit,
                    destinations=dest_infos
                )
                list_plan_responses.append(plan_response)
            return list_plan_responses
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving plans for user ID {user_id}: {e}"
            )
    
    @staticmethod
    async def create_plan(db: AsyncSession, user_id: int, plan_data: PlanCreate) -> PlanResponse:
        try:
            new_plan = await PlanRepository.create_plan(db, plan_data)
            if not new_plan:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create plan"
                )
            
            await PlanRepository.add_plan_member(db, new_plan.id, PlanMemberCreate(user_id=user_id, role=PlanRole.owner))

            return PlanResponse(
                id=new_plan.id,
                place_name=new_plan.place_name,
                start_date=new_plan.start_date,
                end_date=new_plan.end_date,
                budget_limit=new_plan.budget_limit,
                destinations=[]
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error creating plan: {e}"
            )
    
    @staticmethod
    async def update_plan(db: AsyncSession,user_id: int, plan_id: int, updated_data: PlanUpdate):
        try:
            plans = await PlanRepository.get_plan_by_user_id(db, user_id)
            if plans is None:
                plans = []
            
            plan_exists = any(plan.id == plan_id for plan in plans)
            if not plan_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Plan with ID {plan_id} not found or does not belong to user"
                )
            
            updated_plan = await PlanRepository.update_plan(db, plan_id, updated_data)
            if not updated_plan:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Plan with ID {plan_id} not found"
                )
            return PlanResponse(
                id=updated_plan.id,
                place_name=updated_plan.place_name,
                start_date=updated_plan.start_date,
                end_date=updated_plan.end_date,
                budget_limit=updated_plan.budget_limit,
                destinations=[
                    PlanDestinationResponse(
                        id=dest.id,
                        destination_id=dest.destination_id,
                        type=dest.type,
                        visit_date=dest.visit_date,
                        time=dest.time,
                        estimated_cost=dest.estimated_cost,
                        note=dest.note
                    )
                    for dest in await PlanRepository.get_plan_destinations(db, updated_plan.id)
                ]
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error updating plan ID {plan_id}: {e}"
            )
    
    @staticmethod
    async def delete_plan(db: AsyncSession, user_id: int, plan_id: int):
        try:
            is_owner = await PlanRepository.is_plan_owner(db, user_id, plan_id)
            if is_owner == False:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the owner can delete the plan"
                )
            success = await PlanRepository.delete_plan(db, plan_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Plan with ID {plan_id} not found"
                )
            return {"detail": "Plan deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error deleting plan ID {plan_id}: {e}"
            )

    @staticmethod
    async def get_plan_destinations(db: AsyncSession, user_id: int, plan_id: int) -> List[PlanDestinationResponse]:
        try:
            is_member = await PlanRepository.is_member(db, user_id, plan_id)
            if is_member == False:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User is not a member of the plan"
                )
            
            destinations = await PlanRepository.get_plan_destinations(db, plan_id)
            list_dest_responses = [
                PlanDestinationResponse(
                    id=dest.id,
                    destination_id=dest.destination_id,
                    type=dest.type,
                    visit_date=dest.visit_date,
                    time=dest.time,
                    estimated_cost=dest.estimated_cost,
                    note=dest.note
                )
                for dest in destinations
            ]
            return list_dest_responses
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving destinations for plan ID {plan_id}: {e}"
            )

    @staticmethod
    async def add_destination_to_plan(
        db: AsyncSession, 
        plan_id: int,
        data: PlanDestinationCreate,
    ) -> PlanDestinationResponse:
        try:
            plan = await PlanRepository.get_plan_by_id(db, plan_id)
            if not plan:
                raise HTTPException(    
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Plan with ID {plan_id} not found"
                    )
                        
            plan_dest = await PlanRepository.add_destination_to_plan(db, plan_id, data)
            
            if not plan_dest:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to add destination to plan"
                )
            
            return PlanDestinationResponse(
                id=plan_dest.id,
                destination_id=plan_dest.destination_id,
                type=plan_dest.type,
                visit_date=plan_dest.visit_date,
                time=plan_dest.time,
                estimated_cost=plan_dest.estimated_cost,
                note=plan_dest.note
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error adding destination to plan: {e}"
            )
            
    @staticmethod
    async def update_plan_destination(
        db: AsyncSession,
        plan_destination_id: int,
        updated_data: PlanDestinationUpdate
    ) -> PlanDestinationResponse:
        try:
            updated_dest = await PlanRepository.update_plan_destination(
                db, plan_destination_id, updated_data
            )
            if not updated_dest:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Plan destination with ID {plan_destination_id} not found"
                )
            return PlanDestinationResponse(
                id=updated_dest.id,
                destination_id=updated_dest.destination_id,
                type=updated_dest.type,
                visit_date=updated_dest.visit_date,
                time=updated_dest.time,
                estimated_cost=updated_dest.estimated_cost,
                note=updated_dest.note
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error updating plan destination ID {plan_destination_id}: {e}"
            )

    @staticmethod
    async def remove_destination_from_plan(
        db: AsyncSession, 
        plan_destination_id: int,
    ):
        try:
            success = await PlanRepository.remove_destination_from_plan(db, plan_destination_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Destination with ID {plan_destination_id} not found"
                )
            
            return {"detail": "Destination removed from plan successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error removing destination from plan: {e}"
            )
    
    @staticmethod
    async def bulk_add_destinations_to_plan(
        db: AsyncSession,
        plan_id: int,
        destinations: List[PlanDestinationCreate]
    ) -> PlanResponse:
        try:
            plan = await PlanRepository.get_plan_by_id(db, plan_id)
            if not plan:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Plan with ID {plan_id} not found"
                )
            
            added = []
            failed = []
            
            for dest_data in destinations:
                try:
                    plan_dest = await PlanRepository.add_destination_to_plan(db, plan_id, dest_data)
                    if plan_dest:
                        added.append(PlanDestinationResponse(
                            id=plan_dest.id,
                            destination_id=plan_dest.destination_id,
                            type=plan_dest.type,
                            visit_date=plan_dest.visit_date,
                            time=plan_dest.time,
                            estimated_cost=plan_dest.estimated_cost,
                            note=plan_dest.note
                        ))
                    else:
                        failed.append(dest_data.destination_id)
                except Exception:
                    failed.append(dest_data.destination_id)
            
            return PlanResponse(
                id=plan.id,
                place_name=plan.place_name,
                start_date=plan.start_date,
                end_date=plan.end_date,
                budget_limit=plan.budget_limit,
                destinations=await PlanService.get_plan_destinations(db, plan_id)
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error bulk adding destinations to plan: {e}"
            )
    
    @staticmethod
    async def bulk_remove_destinations_from_plan(
        db: AsyncSession,
        plan_id: int,
        plan_destination_ids: List[int]
    ) -> PlanResponse:
        try:
            removed = []
            not_found = []
            
            for plan_dest_id in plan_destination_ids:
                try:
                    success = await PlanRepository.remove_destination_from_plan(db, plan_dest_id)
                    if success:
                        removed.append(plan_dest_id)
                    else:
                        not_found.append(plan_dest_id)
                except Exception:
                    not_found.append(plan_dest_id)
                    
            plan = await PlanRepository.get_plan_by_id(db, plan_id)
                        
            return PlanResponse(
                id=plan.id,
                place_name=plan.place_name,
                start_date=plan.start_date,
                end_date=plan.end_date,
                budget_limit=plan.budget_limit,
                destinations=await PlanService.get_plan_destinations(db, plan.id)
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error bulk removing destinations from plan: {e}"
            )
            
    @staticmethod
    async def get_plan_members(db: AsyncSession, plan_id: int) -> PlanMemberResponse:
        try:
            plan = await PlanRepository.get_plan_by_id(db, plan_id)
            if not plan:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Plan with ID {plan_id} not found"
                )
            user_plans = await PlanRepository.get_plan_members(db, plan_id)
            list_ids = [user_plan.user_id for user_plan in user_plans]
            return PlanMemberResponse(
                plan_id=plan_id,
                ids=list_ids
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving users for plan ID {plan_id}: {e}"
            )
    
    @staticmethod
    async def add_plan_member(db: AsyncSession, user_id: int, plan_id: int, data: MemberCreate) -> PlanMemberResponse:
        try:
            is_owner = await PlanRepository.is_plan_owner(db, user_id, plan_id)
            if is_owner == False:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the owner can add members to the plan"
                )
            duplicates = []
            for id in data.ids:
                if await PlanService.is_member(db, id, plan_id):
                    duplicates.append(id)
                    continue
                await PlanRepository.add_plan_member(db, plan_id, PlanMemberCreate(user_id=id, role=PlanRole.member))
            users = await PlanRepository.get_plan_members(db, plan_id)
            list_ids = [user.user_id for user in users]
            return PlanMemberResponse(
                plan_id=plan_id,
                ids=list_ids
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error associating user with plan: {e}"
            )
            
    @staticmethod
    async def remove_plan_member(db: AsyncSession, user_id: int ,plan_id: int, data: MemberDelete) -> PlanMemberResponse:
        try:
            is_owner = await PlanRepository.is_plan_owner(db, user_id, plan_id)
            if is_owner == False:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the owner can remove members from the plan"
                )
            ids_not_in_plan = []
            for member_id in data.ids:
                if not await PlanService.is_member(db, member_id, plan_id):
                    ids_not_in_plan.append(member_id)
                    continue
                await PlanRepository.remove_plan_member(db, plan_id, member_id)
            list = await PlanService.get_plan_members(db, plan_id)
            ids = list.ids
            return PlanMemberResponse(
                plan_id=plan_id,
                ids=ids
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error removing user from plan: {e}"
            )

    @staticmethod
    async def handle_intent(
        db: AsyncSession,
        user_id: int,
        session_id: int,
        user_text: str
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

            if intent == Intent.ADD:
                destination_id = ent.get("destination_id")
                if not destination_id:
                    return IntentHandlerResponse(ok=False, message="Cần destination_id để thêm.")
                
                visit_date = ent.get("visit_date")
                note = ent.get("note") or ent.get("title") or "Hoạt động mới"
                
                dest_data = PlanDestinationCreate(
                    destination_id=destination_id,
                    destination_type=ent.get("type") or "activity",
                    visit_date=visit_date,
                    note=note
                )
                new_dest = await PlanRepository.add_destination_to_plan(db, plan.id, dest_data)
                if not new_dest:
                    return IntentHandlerResponse(ok=False, message="Không thể thêm destination.")
                
                return IntentHandlerResponse(
                    ok=True,
                    action="add",
                    item={
                        "id": new_dest.id,
                        "destination_id": new_dest.destination_id,
                        "note": new_dest.note
                    }
                )

            if intent == Intent.REMOVE:
                dest_id = ent.get("item_id") or ent.get("destination_id")
                if dest_id:
                    ok = await PlanRepository.remove_destination_from_plan(db, dest_id)
                    return IntentHandlerResponse(ok=ok, action="remove", item_id=dest_id)
                
                return IntentHandlerResponse(ok=False, message="Cần id của destination để xóa.")

            if intent == Intent.MODIFY_TIME:
                dest_id = ent.get("item_id") or ent.get("destination_id")
                time = ent.get("time")
                
                if not dest_id:
                    return IntentHandlerResponse(ok=False, message="Cần id của destination để đổi giờ.")
                
                update_data = PlanDestinationUpdate(time=time)
                updated = await PlanRepository.update_plan_destination(db, dest_id, update_data)
                if not updated:
                    return IntentHandlerResponse(ok=False, message="Không cập nhật được destination.")
                
                return IntentHandlerResponse(
                    ok=True,
                    action="modify_time",
                    item={"id": updated.id, "time": updated.time}
                )

            if intent == Intent.CHANGE_BUDGET:
                budget = ent.get("budget")
                update_data = PlanUpdate(budget_limit=budget)
                updated_plan = await PlanRepository.update_plan(db, plan.id, update_data)
                if not updated_plan:
                    return IntentHandlerResponse(ok=False, message="Không cập nhật được budget.")
                
                return IntentHandlerResponse(ok=True, action="change_budget", budget=budget)

            if intent == Intent.VIEW_PLAN:
                destinations = await PlanRepository.get_plan_destinations(db, plan.id)
                out = [
                    {
                        "id": dest.id,
                        "destination_id": dest.destination_id,
                        "time": dest.time,
                        "visit_date": str(dest.visit_date) if dest.visit_date else None,
                        "note": dest.note
                    }
                    for dest in destinations
                ]
                return IntentHandlerResponse(
                    ok=True,
                    action="view_plan",
                    plan={"id": plan.id, "place_name": plan.place_name, "destinations": out}
                )

            if intent == Intent.SUGGEST:
                suggestions = await RecommendationService.recommend_for_cluster_hybrid(db, user_id)
                return IntentHandlerResponse(ok=True, action="suggest", suggestions=suggestions)

            return IntentHandlerResponse(ok=False, message="Mình không hiểu yêu cầu, bạn nói lại được không?")
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error handling plan intent: {str(e)}"
            )