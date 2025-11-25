from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from models.user import *
from models.mission import *
from schemas.reward_schema import *

class MissionRepository:
    @staticmethod
    async def get_all_missions(db: AsyncSession):
        try:
            result = await db.execute(select(Mission))
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching all missions - {e}")
            return []

    @staticmethod
    async def get_mission_by_id(db: AsyncSession, mission_id: int):
        try:
            result = await db.execute(select(Mission).where(Mission.id == mission_id))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching mission with id {mission_id} - {e}")
            return None
        
    @staticmethod
    async def get_mission_by_name(db: AsyncSession, name: str):
        try:
            result = await db.execute(select(Mission).where(func.lower(Mission.name) == name.lower()))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching mission with name {name} - {e}")
            return None

    @staticmethod
    async def create_mission(db: AsyncSession, mission_data: MissionCreate):
        try:
            new_mission = Mission(
                name=mission_data.name,
                description=mission_data.description,
                reward_type=mission_data.reward_type,
                action_trigger=mission_data.action_trigger,
                value=mission_data.value
            )
            db.add(new_mission)
            await db.commit()
            await db.refresh(new_mission)
            return new_mission
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: creating mission: {mission_data}, {e}")
            return None

    @staticmethod
    async def update_mission(db: AsyncSession, mission_id: int, updated_data: MissionUpdate):
        try:
            result = await db.execute(select(Mission).where(Mission.id == mission_id))
            mission = result.scalar_one_or_none()
            if not mission:
                print(f"WARNING: WARNING: Mission with id {mission_id} not found for update.")
                return None

            if updated_data.name is not None:
                mission.name = updated_data.name
            if updated_data.description is not None:
                mission.description = updated_data.description
            if updated_data.reward_type is not None:
                mission.reward_type = updated_data.reward_type
            if updated_data.action_trigger is not None:
                mission.action_trigger = updated_data.action_trigger
            if updated_data.value is not None:
                mission.value = updated_data.value

            db.add(mission)
            await db.commit()
            await db.refresh(mission)
            return mission
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: updating mission with id {mission_id} - {e}")
            return None

    @staticmethod
    async def delete_mission(db: AsyncSession, mission_id: int):
        try:
            result = await db.execute(select(Mission).where(Mission.id == mission_id))
            mission = result.scalar_one_or_none()
            if not mission:
                return False

            await db.delete(mission)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: deleting mission with id {mission_id} - {e}")
            return False

    @staticmethod
    async def add_mission_to_user(db: AsyncSession, user_id: int, mission_id: int):
        try:
            user = await db.get(User, user_id)
            mission = await db.get(Mission, mission_id)
            if not user or not mission:
                print(f"WARNING: User or Mission not found (user={user_id}, mission={mission_id})")
                return None

            existing = await MissionRepository.completed_mission(db, user_id, mission_id)
            if existing:
                print("WARNING: User already completed this mission")
                return existing

            new_user_mission = UserMission(
                user_id=user_id,
                mission_id=mission_id,
                completed_at=func.now()
            )
            db.add(new_user_mission)
            await db.commit()
            await db.refresh(new_user_mission)
            return new_user_mission
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: while adding mission to user - {e}")
            return None

    @staticmethod
    async def get_all_missions_by_user(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(
                select(UserMission).where(UserMission.user_id == user_id)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching user badges for user {user_id} - {e}")
            return []

    @staticmethod
    async def completed_mission(db: AsyncSession, user_id: int, mission_id: int):
        try:
            result = await db.execute(
                select(UserMission)
                .where(UserMission.user_id == user_id, UserMission.mission_id == mission_id)
            )
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            print(f"ERROR: checking if user has completed mission - {e}")
            return False

    @staticmethod
    async def remove_user_mission(db: AsyncSession, user_id: int, mission_id: int):
        try:
            result = await db.execute(
                select(UserMission).where(
                    UserMission.user_id == user_id,
                    UserMission.mission_id == mission_id
                )
            )
            user_mission = result.scalar_one_or_none()
            if not user_mission:
                print(f"WARNING: WARNING: Mission {mission_id} not found for user {user_id}.")
                return False

            await db.delete(user_mission)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: deleting mission for user {user_id} - {e}")
            return False
