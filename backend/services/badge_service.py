from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from repository.badge_repository import BadgeRepository
from schema.badge_schema import BadgeCreate, BadgeUpdate

class BadgeService:
    @staticmethod
    async def get_all_badges(db: AsyncSession):
        try:
            badges = await BadgeRepository.get_all_badges(db)
            return badges
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving all badges: {e}"
            )
        
    @staticmethod
    async def get_badge_by_id(db: AsyncSession, badge_id: int):
        try:
            badge = await BadgeRepository.get_badge_by_id(db, badge_id)
            if not badge:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Badge with ID {badge_id} not found"
                )
            return badge
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving badge by ID {badge_id}: {e}"
            )

    @staticmethod
    async def get_badge_by_name(db: AsyncSession, name: str):
        try:
            badge = await BadgeRepository.get_badge_by_name(db, name)
            if not badge:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Badge with name '{name}' not found"
                )
            return badge
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving badge by name '{name}': {e}"
            )
        
    @staticmethod
    async def create_badge(db: AsyncSession, badge_data: BadgeCreate):
        try:
            existing = await BadgeRepository.get_badge_by_name(db, badge_data.name)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Badge name already exists"
                )
            new_badge = await BadgeRepository.create_badge(db, badge_data)
            if not new_badge:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create badge"
                )
            return new_badge
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error creating badge: {e}"
            )
        
    @staticmethod
    async def update_badge(db: AsyncSession, badge_id: int, updated_data: BadgeUpdate):
        try:
            badge = await BadgeRepository.get_badge_by_id(db, badge_id)
            if not badge:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Badge with ID {badge_id} not found"
                )
            updated_badge = await BadgeRepository.update_badge(db, badge_id, updated_data)
            if not updated_badge:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update badge"
                )
            return updated_badge
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error updating badge ID {badge_id}: {e}"
            )

    @staticmethod
    async def delete_badge(db: AsyncSession, badge_id: int):
        try:
            badge = await BadgeRepository.get_badge_by_id(db, badge_id)
            if not badge:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Badge with ID {badge_id} not found"
                )
            result = await BadgeRepository.delete_badge(db, badge_id)
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete badge"
                )
            return {"detail": "Badge deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error deleting badge ID {badge_id}: {e}"
            )