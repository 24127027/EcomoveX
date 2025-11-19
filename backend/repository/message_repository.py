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
            await db.rollback()
            print(f"ERROR: fetching message ID {message_id} - {e}")
            return None

    @staticmethod
    async def get_message_by_keyword(db: AsyncSession, user_id: int, keyword: str):
        try:
            result = await db.execute(
                select(Message).where(
                    Message.content.ilike(f"%{keyword}%"),
                    (Message.sender_id == user_id) | (Message.receiver_id == user_id)
                )
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: fetching message with content '{keyword}' for user {user_id} - {e}")
            return None

    @staticmethod
    async def create_message(db: AsyncSession, sender_id: int, receiver_id: int, message_data: MessageCreate):
        try:
            new_message = Message(
                sender_id=sender_id,
                receiver_id=receiver_id,
                content=message_data.content,
                message_type=message_data.message_type
            )
            new_message.created_at = func.now()
            db.add(new_message)
            await db.commit()
            await db.refresh(new_message)
            return new_message
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: creating message - {e}")
            return None
    
    @staticmethod
    async def delete_message(db: AsyncSession, sender_id: int, message_id: int):
        try:
            result = await db.execute(select(Message).where(Message.id == message_id, Message.sender_id == sender_id))
            message = result.scalar_one_or_none()
            if message:
                await db.delete(message)
                await db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: deleting message ID {message_id} by sender {sender_id} - {e}")
            return False