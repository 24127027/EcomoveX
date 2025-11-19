from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from repository.destination_repository import DestinationRepository
from repository.plan_repository import PlanRepository
from schemas.plan_schema import *

class PlanService:
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
                        destination_id=dest.destination_id,
                        type=dest.type,
                        visit_date=dest.visit_date,
                        note=dest.note
                    )
                    for dest in destinations
                ]
                plan_response = PlanResponse(
                    id=plan.id,
                    user_id=plan.user_id,
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
            new_plan = await PlanRepository.create_plan(db, user_id, plan_data)
            if not new_plan:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create plan"
                )
            return PlanResponse(
                id=new_plan.id,
                user_id=new_plan.user_id,
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
                user_id=updated_plan.user_id,
                place_name=updated_plan.place_name,
                start_date=updated_plan.start_date,
                end_date=updated_plan.end_date,
                budget_limit=updated_plan.budget_limit,
                destinations=[
                    PlanDestinationResponse(
                        destination_id=dest.destination_id,
                        type=dest.type,
                        visit_date=dest.visit_date,
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
            plans = await PlanRepository.get_plan_by_user_id(db, user_id)
            if plans is None:
                plans = []
            
            plan_exists = any(plan.id == plan_id for plan in plans)
            if not plan_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Plan with ID {plan_id} not found or does not belong to user"
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
    async def get_plan_destinations(db: AsyncSession, plan_id: int, user_id: int) -> List[PlanDestinationResponse]:
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
            
            destinations = await PlanRepository.get_plan_destinations(db, plan_id)
            list_dest_responses = [
                PlanDestinationResponse(
                    destination_id=dest.destination_id,
                    type=dest.type,
                    visit_date=dest.visit_date,
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
                destination_id=plan_dest.destination_id,
                type=plan_dest.type,
                visit_date=plan_dest.visit_date,
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
        destination_id: str,
        updated_data: PlanDestinationUpdate
    ) -> PlanDestinationResponse:
        try:
            updated_dest = await PlanRepository.update_plan_destination(
                db, destination_id, updated_data
            )
            if not updated_dest:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Destination with ID {destination_id} not found"
                )
            return PlanDestinationResponse(
                destination_id=updated_dest.destination_id,
                type=updated_dest.type,
                visit_date=updated_dest.visit_date,
                note=updated_dest.note
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error updating destination ID {destination_id}: {e}"
            )

    @staticmethod
    async def remove_destination_from_plan(
        db: AsyncSession, 
        destination_id: str,
    ):
        try:
            success = await PlanRepository.remove_destination_from_plan(db, destination_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Destination with ID {destination_id} not found"
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
    async def get_user_plans(db: AsyncSession, plan_id: int) -> UserPlanResponse:
        try:
            plan = await PlanRepository.get_plan_by_id(db, plan_id)
            if not plan:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Plan with ID {plan_id} not found"
                )
            user_plans = await PlanRepository.get_user_plans(db, plan_id)
            list_ids = [user_plan.user_id for user_plan in user_plans]
            return UserPlanResponse(
                user_id=plan.user_id,
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
    async def add_user_plan(db: AsyncSession, plan_id: int, data: UserPlansCreate) -> UserPlanResponse:
        try:
            plan = await PlanRepository.get_plan_by_id(db, plan_id)
            for user_id in data.ids:
                if plan.user_id == user_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Owner of the plan cannot be added as a user"
                    )
                user_plan = await PlanRepository.add_user_plan(db, user_id, plan_id)
                if not user_plan:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to associate user with plan"
                    )
            users = await PlanRepository.get_user_plans(db, plan_id)
            list_ids = [user.user_id for user in users]
            return UserPlanResponse(
                user_id=user_plan.user_id,
                plan_id=user_plan.plan_id,
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
    async def remove_user_plan(db: AsyncSession, plan_id: int, data: UserPlanDelete):
        try:
            for user_id in data.ids:
                success = await PlanRepository.remove_user_plan(db, user_id, plan_id)
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"User plan with ID {user_id} not found"
                    )
            return {"detail": "User removed from plan successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error removing user from plan: {e}"
            )