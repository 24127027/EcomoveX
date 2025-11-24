from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from models.room import *

class RoomRepository:
    @staticmethod
    async def is_owner(db: AsyncSession, user_id: int, room_id: int) -> bool:
        try:
            result = await db.execute(
                select(RoomMember).where(
                    RoomMember.room_id == room_id,
                    RoomMember.user_id == user_id,
                    RoomMember.role == MemberRole.admin
                )
            )
            room = result.scalar_one_or_none()
            return room is not None
        except SQLAlchemyError as e:
            print(f"ERROR: checking ownership of user ID {user_id} for room ID {room_id} - {e}")
            return False
        
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
            if member:
                return True
            result_direct = await db.execute(
                select(RoomDirect).where(
                    (RoomDirect.room_id == room_id) & 
                    ((RoomDirect.user1_id == user_id) | (RoomDirect.user2_id == user_id))
                )
            )
            direct_member = result_direct.scalar_one_or_none()
            return direct_member is not None

        except SQLAlchemyError as e:
            print(f"ERROR: checking membership of user ID {user_id} in room ID {room_id} - {e}")
            return False

    @staticmethod
    async def list_rooms_for_user(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(
                select(Room).join(RoomMember).where(
                    RoomMember.user_id == user_id,
                    Room.room_type == RoomType.group)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: listing rooms for user ID {user_id} - {e}")
            return []
        
    @staticmethod
    async def list_direct_rooms_for_user(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(
                select(Room).join(RoomDirect).where(
                    (RoomDirect.user1_id == user_id) | (RoomDirect.user2_id == user_id)
                )
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: listing direct rooms for user ID {user_id} - {e}")
            return []
    
    @staticmethod
    async def get_direct_room_between_users(db: AsyncSession, user1_id: int, user2_id: int):
        try:
            result = await db.execute(
                select(Room).join(RoomDirect).where(
                    (RoomDirect.user1_id == user1_id) & (RoomDirect.user2_id == user2_id)
                )
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"ERROR: retrieving direct room between user ID {user1_id} and user ID {user2_id} - {e}")
            return None
    
    @staticmethod
    async def get_room_by_id(db: AsyncSession, room_id: int):
        try:
            result = await db.execute(select(Room).where(Room.id == room_id))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"ERROR: retrieving room ID {room_id} - {e}")
            return None
        
    @staticmethod
    async def create_room(db: AsyncSession, name: str):
        try:
            new_room = Room(
                name=name,
                room_type=RoomType.group
                )  
            db.add(new_room)
            await db.commit()
            await db.refresh(new_room)
            return new_room
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: creating room '{name}' - {e}")
            return None
        
    @staticmethod
    async def create_direct_room(db: AsyncSession, user1_id: int, user2_id: int):
        try:
            new_room = Room(
                room_type=RoomType.direct
            )
            db.add(new_room)
            await db.commit()
            await db.refresh(new_room)
            room_direct = RoomDirect(
                room_id=new_room.id,
                user1_id=min(user1_id, user2_id),
                user2_id=max(user1_id, user2_id)
            )
            db.add(room_direct)
            await db.commit()
            await db.refresh(room_direct)
            return new_room
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: creating direct room between user ID {user1_id} and user ID {user2_id} - {e}")
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
    async def list_user_rooms(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(
                select(Room).join(RoomMember).where(RoomMember.user_id == user_id)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: listing rooms for user ID {user_id} - {e}")
            return []