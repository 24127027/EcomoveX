from certifi import where
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from models.room import *

class RoomRepository:
    @staticmethod
    async def get_room_by_id(db: AsyncSession, user_id: int, room_id: int):
        try:
            result = await db.execute(where(Room.id == room_id))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"ERROR: retrieving room ID {room_id} for user ID {user_id} - {e}")
            return None
        
    @staticmethod
    async def create_room(db: AsyncSession, name: str):
        try:
            new_room = Room(name=name)
            db.add(new_room)
            await db.commit()
            await db.refresh(new_room)
            return new_room
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: creating room '{name}' - {e}")
            return None

    @staticmethod
    async def add_member(db: AsyncSession, user_id: int, room_id: int):
        try:
            new_member = RoomMember(room_id=room_id, user_id=user_id)
            db.add(new_member)
            await db.commit()
            await db.refresh(new_member)
            return new_member
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: adding user ID {user_id} to room ID {room_id} - {e}")
            return None
    
    @staticmethod
    async def remove_member(db: AsyncSession, user_id: int, room_id: int):
        try:
            result = await db.execute(
                select(RoomMember).where(
                    RoomMember.room_id == room_id,
                    RoomMember.user_id == user_id
                )
            )
            member = result.scalar_one_or_none()
            if member:
                await db.delete(member)
                await db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: removing user ID {user_id} from room ID {room_id} - {e}")
            return False
        
    @staticmethod
    async def list_members(db: AsyncSession, room_id: int):
        try:
            result = await db.execute(
                select(RoomMember).where(RoomMember.room_id == room_id)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: listing members for room ID {room_id} - {e}")
            return []
        
    @staticmethod
    async def is_member(db: AsyncSession, user_id: int, room_id: int) -> bool:
        try:
            result = await db.execute(
                select(RoomMember).where(
                    RoomMember.room_id == room_id,
                    RoomMember.user_id == user_id
                )
            )
            member = result.scalar_one_or_none()
            return member is not None
        except SQLAlchemyError as e:
            print(f"ERROR: checking membership of user ID {user_id} in room ID {room_id} - {e}")
            return False
        
    @staticmethod
    async def list_user_rooms(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(
                select(Room).join(RoomMember).where(RoomMember.user_id == user_id)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: listing rooms for user ID {user_id} - {e}")
            return []