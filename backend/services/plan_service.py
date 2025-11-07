from fastapi import HTTPException, status
from repository.plan_repository import PlanRepository
from repository.destination_repository import DestinationRepository
from sqlalchemy.ext.asyncio import AsyncSession
from schema.plan_schema import PlanRequestCreate, PlanRequestUpdate

# Note: PlanService uses user database (get_db)
# For operations involving destinations, pass destination_db separately

class PlanService:
    @staticmethod
    async def get_plans_by_user(db: AsyncSession, user_id: int):
        try:
            plans = await PlanRepository.get_plan_by_user_id(db, user_id)
            if plans is None:
                return []
            return plans
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving plans for user ID {user_id}: {e}"
            )
    
    @staticmethod
    async def create_plan(db: AsyncSession, user_id: int, plan_data: PlanRequestCreate):
        try:
            new_plan = await PlanRepository.create_plan(db, user_id, plan_data)
            if not new_plan:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create plan"
                )
            return new_plan
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error creating plan: {e}"
            )
    
    @staticmethod
    async def update_plan(db: AsyncSession, plan_id: int, updated_data: PlanRequestUpdate, user_id: int):
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
            return updated_plan
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error updating plan ID {plan_id}: {e}"
            )
    
    @staticmethod
    async def delete_plan(db: AsyncSession, plan_id: int, user_id: int):
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

    # PlanDestination methods (require both user_db and destination_db)
    @staticmethod
    async def get_plan_destinations(db: AsyncSession, plan_id: int, user_id: int):
        """Get all destinations for a user's plan"""
        try:
            # Verify plan belongs to user
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
            return destinations
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving destinations for plan ID {plan_id}: {e}"
            )

    @staticmethod
    async def add_destination_to_plan(
        user_db: AsyncSession, 
        destination_db: AsyncSession,
        plan_id: int, 
        destination_id: int,
        destination_type: str,
        visit_date,
        note: str = None,
        user_id: int = None
    ):
        """
        Add a destination to a plan with validation.
        Requires both user_db and destination_db sessions.
        """
        try:
            # Verify plan exists and belongs to user (if user_id provided)
            if user_id:
                plans = await PlanRepository.get_plan_by_user_id(user_db, user_id)
                if plans is None:
                    plans = []
                
                plan_exists = any(plan.id == plan_id for plan in plans)
                if not plan_exists:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Plan with ID {plan_id} not found or does not belong to user"
                    )
            
            # Verify destination exists in destination database
            destination = await DestinationRepository.get_destination_by_id(
                destination_db, 
                destination_id
            )
            if not destination:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Destination with ID {destination_id} not found"
                )
            
            # Add destination to plan
            plan_dest = await PlanRepository.add_destination_to_plan(
                user_db, 
                plan_id, 
                destination_id, 
                destination_type, 
                visit_date, 
                note
            )
            
            if not plan_dest:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to add destination to plan"
                )
            
            return plan_dest
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error adding destination to plan: {e}"
            )

    @staticmethod
    async def remove_destination_from_plan(
        db: AsyncSession, 
        plan_destination_id: int,
        user_id: int = None
    ):
        """Remove a destination from a plan"""
        try:
            # Optional: verify the plan belongs to the user
            # This would require getting the plan_destination first to get plan_id
            
            success = await PlanRepository.remove_destination_from_plan(db, plan_destination_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Plan destination with ID {plan_destination_id} not found"
                )
            
            return {"detail": "Destination removed from plan successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error removing destination from plan: {e}"
            )
