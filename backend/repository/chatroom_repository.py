from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.exc import SQLAlchemyError
from models.chat_room import ChatRoom, ChatRoomMember
from datetime import datetime
from typing import List

class ChatRoomRepository:
    @staticmethod
    async def get_room_by_user_id(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(
                select(ChatRoom).join(ChatRoomMember).where(ChatRoomMember.user_id == user_id)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error fetching chat rooms for user ID {user_id}: {e}")
            return None

    @staticmethod
    async def create_room(db: AsyncSession, room_name: str, member_ids: List[int]):
        try:
            new_room = ChatRoom(
                name=room_name
            )

            new_room.created_at = datetime.utcnow()
            db.add(new_room)
            await db.commit()
            await db.refresh(new_room)

            for user_id in member_ids:
                member = ChatRoomMember(
                    chat_room_id=new_room.id,
                    user_id=user_id,
                    joined_at=datetime.utcnow()
                )
                db.add(member)

            await db.commit()
            return new_room
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error creating chat room: {e}")
            return None

    @staticmethod
    async def update_room(db: AsyncSession, room_id: int, new_room_name: str):
        try:
            result = await db.execute(select(ChatRoom).where(ChatRoom.id == room_id))
            room = result.scalar_one_or_none()
            if not room:
                print(f"Chat room ID {room_id} not found")
                return None

            room.name = new_room_name

            db.add(room)
            await db.commit()
            await db.refresh(room)
            return room
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error updating chat room ID {room_id}: {e}")
            return None

    @staticmethod
    async def delete_room(db: AsyncSession, room_id: int):
        try:
            result = await db.execute(select(ChatRoom).where(ChatRoom.id == room_id))
            room = result.scalar_one_or_none()
            if not room:
                print(f"Chat room ID {room_id} not found")
                return False

            await db.delete(room)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error deleting chat room ID {room_id}: {e}")
            return False


class ChatRoomMemberRepository:
    @staticmethod
    async def add_member(db: AsyncSession, room_id: int, user_id: int):
        try:
            result = await db.execute(
                select(ChatRoomMember).where(
                    ChatRoomMember.chat_room_id == room_id,
                    ChatRoomMember.user_id == user_id,
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                print("User already in chat room.")
                return existing

            new_member = ChatRoomMember(
                chat_room_id=room_id,
                user_id=user_id,
                joined_at=datetime.utcnow(),
            )
            db.add(new_member)
            await db.commit()
            await db.refresh(new_member)
            return new_member
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error adding member to chat room {room_id}: {e}")
            return None
    
    @staticmethod
    async def bulk_add_members(db: AsyncSession, room_id: int, user_ids: List[int]):
        try:
            new_members = []
            for user_id in user_ids:
                result = await db.execute(
                    select(ChatRoomMember).where(
                        ChatRoomMember.chat_room_id == room_id,
                        ChatRoomMember.user_id == user_id,
                    )
                )
                existing = result.scalar_one_or_none()
                if not existing:
                    new_member = ChatRoomMember(
                        chat_room_id=room_id,
                        user_id=user_id,
                        joined_at=datetime.utcnow(),
                    )
                    db.add(new_member)
                    new_members.append(new_member)

            await db.commit()
            for member in new_members:
                await db.refresh(member)
            return new_members
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error bulk adding members to chat room {room_id}: {e}")
            return []

    @staticmethod
    async def get_members(db: AsyncSession, room_id: int):
        try:
            result = await db.execute(
                select(ChatRoomMember).where(ChatRoomMember.chat_room_id == room_id)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error fetching members for room {room_id}: {e}")
            return []

    @staticmethod
    async def remove_member(db: AsyncSession, room_id: int, user_id: int):
        try:
            result = await db.execute(
                select(ChatRoomMember).where(
                    ChatRoomMember.chat_room_id == room_id,
                    ChatRoomMember.user_id == user_id,
                )
            )
            member = result.scalar_one_or_none()
            if not member:
                print("Member not found in chat room.")
                return False

            await db.delete(member)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error removing member from room {room_id}: {e}")
            return False
        
    @staticmethod
    async def bulk_remove_members(db: AsyncSession, room_id: int, user_ids: List[int]):
        try:
            for user_id in user_ids:
                result = await db.execute(
                    select(ChatRoomMember).where(
                        ChatRoomMember.chat_room_id == room_id,
                        ChatRoomMember.user_id == user_id,
                    )
                )
                member = result.scalar_one_or_none()
                if member:
                    await db.delete(member)

            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error bulk removing members from room {room_id}: {e}")
            return False
