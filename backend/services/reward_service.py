from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from repository.badge_repository import BadgeRepository, UserBadgeRepository
from user_service import UserService
from schema.reward_schema import RewardType, RewardCreate

class RewardService:
    @staticmethod
    async def award_badge_to_user(db: AsyncSession, user_id: int, badge_name: str):
        try:
            user = await UserService.get_user_by_id(db, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found"
                )

            badge = await BadgeRepository.get_badge_by_name(db, badge_name)
            if not badge:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Badge '{badge_name}' not found"
                )

            user_badge = await UserBadgeRepository.create_user_badge(db, user_id, badge.id)
            if not user_badge:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to award badge to user"
                )
            return user_badge
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error awarding badge '{badge_name}' to user ID {user_id}: {e}"
            )
        
    @staticmethod
    async def add_reward(db: AsyncSession, user_id: int, reward: RewardCreate):
        try:
            user = await UserService.get_user_by_id(db, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found"
                )

            if reward.type == RewardType.eco_point:
                updated_user = await UserService.add_eco_point(db, user_id, reward.value)
                if not updated_user:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to update eco points"
                    )
                return updated_user
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unsupported reward type"
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error adding reward to user ID {user_id}: {e}"
            )