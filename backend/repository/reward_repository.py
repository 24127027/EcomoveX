from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from models.user import User
from models.reward import Reward, UserReward

class UserRewardRepository:
    @staticmethod
    async def add_reward_to_user(db: AsyncSession, user_id: int, reward_id: int):
        try:
            user = await db.get(User, user_id)
            reward = await db.get(Reward, reward_id)
            if not user or not reward:
                print(f"User or Reward not found (user={user_id}, reward={reward_id})")
                return None

            result = await db.execute(
                select(UserReward).where(
                    UserReward.user_id == user_id,
                    UserReward.reward_id == reward_id
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                print("User already owns this reward.")
                return existing

            new_user_reward = UserReward(
                user_id=user_id,
                reward_id=reward_id,
                obtained_at=datetime.utcnow(),
            )
            db.add(new_user_reward)

            if hasattr(user, "eco_point") and hasattr(reward, "value"):
                user.eco_point = (user.eco_point or 0) + (reward.value or 0)
                db.add(user)

            await db.commit()
            await db.refresh(new_user_reward)
            return new_user_reward

        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error while adding reward to user: {e}")
            return None

    @staticmethod
    async def get_user_rewards(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(
                select(UserReward).where(UserReward.user_id == user_id)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error fetching user rewards for user {user_id}: {e}")
            return []

    @staticmethod
    async def has_reward(db: AsyncSession, user_id: int, reward_id: int):
        try:
            result = await db.execute(
                select(UserReward)
                .where(UserReward.user_id == user_id, UserReward.reward_id == reward_id)
            )
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            print(f"Error checking if user has reward: {e}")
            return False

    @staticmethod
    async def remove_user_reward(db: AsyncSession, user_id: int, reward_id: int):
        try:
            result = await db.execute(
                select(UserReward).where(
                    UserReward.user_id == user_id,
                    UserReward.reward_id == reward_id
                )
            )
            user_reward = result.scalar_one_or_none()
            if not user_reward:
                print("Không tìm thấy reward để xóa.")
                return False

            await db.delete(user_reward)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Lỗi khi xóa reward của user {user_id}: {e}")
            return False