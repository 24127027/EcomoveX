from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from models.message import *
from schemas.message_schema import *

class MessageRepository:
    @staticmethod
    async def get_message_by_id(db: AsyncSession, message_id: int):
        try:
            result = await db.execute(select(Message).where(Message.id == message_id))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching message ID {message_id} - {e}")
            return None

    @staticmethod
    async def get_messages_by_room(db: AsyncSession, room_id: int):
        try:
            result = await db.execute(
                select(Message).where(
                    (Message.room_id == room_id)
                ).order_by(Message.created_at.desc())
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching messages for room ID {room_id} - {e}")
            return []
        
    @staticmethod
    async def search_messages_by_keyword(db: AsyncSession, room_id: int, keyword: str):
        try:
            result = await db.execute(
                select(Message).where(
                    (Message.content.ilike(f"%{keyword}%")) &
                    (Message.room_id == room_id)
                ).order_by(Message.created_at.desc())
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: searching messages for room ID {room_id} with keyword '{keyword}' - {e}")
            return []
        
    @staticmethod
    async def create_message(db: AsyncSession, sender_id: int, room_id: int, message_data: MessageCreate):
        try:
            new_message = Message(
                sender_id=sender_id,
                room_id=room_id,
                message_type=message_data.message_type,
                content=message_data.content,
                status=MessageStatus.sent
            )
            db.add(new_message)
            await db.commit()
            await db.refresh(new_message)
            return new_message
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: creating message from sender ID {sender_id} - {e}")
            return None
        
    @staticmethod
    async def update_message_status(db: AsyncSession, message_id: int, new_status: MessageStatus):
        try:
            message = await MessageRepository.get_message_by_id(db, message_id)
            if not message:
                print(f"WARNING: Message not found with ID {message_id}")
                return None
            message.status = new_status
            db.add(message)
            await db.commit()
            await db.refresh(message)
            return message
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: updating status for message ID {message_id} - {e}")
            return None
        
    @staticmethod
    async def update_message_content(db: AsyncSession, message_id: int, new_content: str):
        try:
            message = await MessageRepository.get_message_by_id(db, message_id)
            if not message:
                print(f"WARNING: Message not found with ID {message_id}")
                return None
            message.content = new_content
            db.add(message)
            await db.commit()
            await db.refresh(message)
            return message
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: updating content for message ID {message_id} - {e}")
            return None
        
    @staticmethod
    async def delete_message(db: AsyncSession, user_id: int, message_id: int):
        try:
            result = await db.execute(
                select(Message).where(
                    (Message.id == message_id) &
                    (Message.sender_id == user_id)
                )
            )
            message = result.scalar_one_or_none()
            if message:
                await db.delete(message)
                await db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: deleting message ID {message_id} by user ID {user_id} - {e}")
            return False