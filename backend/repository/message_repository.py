from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.exc import SQLAlchemyError
from models.message import Message
from datetime import datetime, UTC
from schema.message_schema import MessageCreate, MessageUpdate

class MessageRepository:
    @staticmethod
    async def get_message_by_id(db: AsyncSession, message_id: int):
        try:
            result = await db.execute(select(Message).where(Message.id == message_id))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error fetching message ID {message_id}: {e}")
            return None

    @staticmethod
    async def get_message_by_keyword(db: AsyncSession, keyword: str, user_id: int):
        try:
            result = await db.execute(select(Message).where(Message.content.ilike(f"%{keyword}%"), Message.user_id == user_id))
            return result.scalars().all()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error fetching message with content '{keyword}' for user {user_id}: {e}")
            return None

    @staticmethod
    async def create_message(db: AsyncSession, message_data: MessageCreate, user_id: int):
        try:
            new_message = Message(
                user_id=user_id,
                sender=message_data.sender,
                content=message_data.content,
                message_type=message_data.message_type
            )
            new_message.created_at = datetime.now(UTC).replace(tzinfo=None)
            db.add(new_message)
            await db.commit()
            await db.refresh(new_message)
            return new_message
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error creating message: {e}")
            return None
    
    @staticmethod
    async def update_message(db: AsyncSession, message_id: int, updated_data: MessageUpdate):
        try:
            result = await db.execute(select(Message).where(Message.id == message_id))
            message = result.scalar_one_or_none()
            if not message:
                print(f"Message ID {message_id} not found")
                return None

            if updated_data.content is not None:
                message.content = updated_data.content

            db.add(message)
            await db.commit()
            await db.refresh(message)
            return message
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error updating message ID {message_id}: {e}")
            return None

    @staticmethod
    async def delete_message(db: AsyncSession, message_id: int):
        try:
            result = await db.execute(select(Message).where(Message.id == message_id))
            message = result.scalar_one_or_none()
            if not message:
                print(f"Message ID {message_id} not found")
                return False

            await db.delete(message)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error deleting message ID {message_id}: {e}")
            return False