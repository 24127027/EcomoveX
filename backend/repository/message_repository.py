from typing import Any, Dict, Optional

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.message import *
from schemas.message_schema import *


class MessageRepository:
    @staticmethod
    async def get_message_by_id(db: AsyncSession, message_id: int):
        try:
            result = await db.execute(
                select(Message)
                .options(selectinload(Message.file_metadata))
                .where(Message.id == message_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching message ID {message_id} - {e}")
            return None

    @staticmethod
    async def get_messages_by_room(db: AsyncSession, room_id: int):
        try:
            result = await db.execute(
                select(Message)
                .options(selectinload(Message.file_metadata))
                .where((Message.room_id == room_id))
                .order_by(Message.created_at.desc())
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching messages for room ID {room_id} - {e}")
            return []

    @staticmethod
    async def get_file_messages_by_room(db: AsyncSession, room_id: int):
        try:
            result = await db.execute(
                select(Message)
                .where((Message.room_id == room_id) & (Message.message_type == MessageType.file))
                .order_by(Message.created_at.desc())
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching file messages for room ID {room_id} - {e}")
            return []

    @staticmethod
    async def search_messages_by_keyword(db: AsyncSession, room_id: int, keyword: str):
        try:
            result = await db.execute(
                select(Message)
                .options(selectinload(Message.file_metadata))
                .where((Message.content.ilike(f"%{keyword}%")) & (Message.room_id == room_id))
                .order_by(Message.created_at.desc())
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: searching messages for room ID {room_id} with keyword '{keyword}' - {e}")
            return []

    @staticmethod
    async def create_text_message(
        db: AsyncSession, sender_id: int, room_id: int, message_text: str
    ):
        try:
            new_message = Message(
                sender_id=sender_id,
                room_id=room_id,
                message_type=MessageType.text,
                content=message_text,
                file_blob_name=None,
                status=MessageStatus.sent,
            )
            db.add(new_message)
            await db.commit()
            await db.refresh(new_message)
            return new_message
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: creating text message - {e}")
            return None

    @staticmethod
    async def create_file_message(
        db: AsyncSession, sender_id: int, room_id: int, file_blob_name: str
    ):
        try:
            new_message = Message(
                sender_id=sender_id,
                room_id=room_id,
                message_type=MessageType.file,
                content=None,
                file_blob_name=file_blob_name,
                status=MessageStatus.sent,
            )
            db.add(new_message)
            await db.commit()
            await db.refresh(new_message)
            return new_message
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: creating file message - {e}")
            return None

    @staticmethod
    async def create_invitation_message(
        db: AsyncSession, sender_id: int, room_id: int, plan_id: int, message_text: str
    ):
        try:
            new_message = Message(
                sender_id=sender_id,
                room_id=room_id,
                plan_id=plan_id,
                message_type=MessageType.invitation,
                content=message_text,
                file_blob_name=None,
                status=MessageStatus.sent,
            )
            db.add(new_message)
            await db.commit()
            await db.refresh(new_message)
            return new_message
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: creating invitation message - {e}")
            return None

    @staticmethod
    async def update_message_status(db: AsyncSession, message_id: int, new_status: MessageStatus):
        try:
            stmt = (
                update(Message)
                .where(Message.id == message_id)
                .values(status=new_status)
                .returning(Message)
            )
            result = await db.execute(stmt)
            await db.commit()

            message = result.scalar_one_or_none()
            if message:
                await db.refresh(message)
            return message
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: updating status for message ID {message_id} - {e}")
            return None

    @staticmethod
    async def update_message_content(db: AsyncSession, message_id: int, new_content: str):
        try:
            stmt = (
                update(Message)
                .where(
                    and_(
                        Message.id == message_id,
                    )
                )
                .values(content=new_content)
                .returning(Message)
            )
            result = await db.execute(stmt)
            await db.commit()

            message = result.scalar_one_or_none()
            if message:
                await db.refresh(message)
            return message
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: updating content for message ID {message_id} - {e}")
            return None

    @staticmethod
    async def delete_message(db: AsyncSession, message_id: int):
        try:
            stmt = delete(Message).where(
                and_(
                    Message.id == message_id,
                )
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: deleting message ID {message_id} - {e}")
            return False

    @staticmethod
    async def save_room_context(
        db: AsyncSession, context_data: RoomContextCreate
    ) -> Optional[RoomContext]:
        try:
            query = select(RoomContext).where(
                and_(
                    RoomContext.room_id == context_data.room_id,
                    RoomContext.key == context_data.key,
                )
            )
            result = await db.execute(query)
            context = result.scalars().first()

            if context:
                context.value = context_data.value
                context.updated_at = func.now()
            else:
                context = RoomContext(
                    room_id=context_data.room_id,
                    key=context_data.key,
                    value=context_data.value,
                )
                db.add(context)

            await db.commit()
            await db.refresh(context)
            return context
        except SQLAlchemyError as e:
            await db.rollback()
            print(
                f"ERROR: Saving room context for room {context_data.room_id}, key {context_data.key} - {e}"
            )
            return None

    @staticmethod
    async def get_room_context(db: AsyncSession, room_id: int, key: str) -> Optional[Any]:
        try:
            query = select(RoomContext).where(
                and_(RoomContext.room_id == room_id, RoomContext.key == key)
            )
            result = await db.execute(query)
            context = result.scalars().first()
            return context.value if context else None
        except SQLAlchemyError as e:
            print(f"ERROR: Getting context for room {room_id}, key {key} - {e}")
            return None

    @staticmethod
    async def load_room_context(db: AsyncSession, room_id: int) -> Dict[str, Any]:
        try:
            query = select(RoomContext).where(RoomContext.room_id == room_id)
            result = await db.execute(query)
            contexts = result.scalars().all()
            return {context.key: context.value for context in contexts}
        except SQLAlchemyError as e:
            print(f"ERROR: Loading room context for room {room_id} - {e}")
            return {}

    @staticmethod
    async def delete_room_context(db: AsyncSession, room_id: int, key: str) -> bool:
        try:
            stmt = delete(RoomContext).where(
                and_(RoomContext.room_id == room_id, RoomContext.key == key)
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Deleting context for room {room_id}, key {key} - {e}")
            return False

    @staticmethod
    async def clear_room_context(db: AsyncSession, room_id: int) -> bool:
        try:
            stmt = delete(RoomContext).where(RoomContext.room_id == room_id)
            await db.execute(stmt)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Clearing context for room {room_id} - {e}")
            return False

    @staticmethod
    async def get_message_count_by_room(db: AsyncSession, room_id: int):
        try:
            result = await db.execute(
                select(func.count(Message.id)).where(Message.room_id == room_id)
            )
            return result.scalar() or 0
        except SQLAlchemyError as e:
            print(f"ERROR: counting messages for room {room_id} - {e}")
            return 0

    @staticmethod
    async def get_latest_message_by_room(db: AsyncSession, room_id: int):
        try:
            result = await db.execute(
                select(Message)
                .where(Message.room_id == room_id)
                .order_by(Message.created_at.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"ERROR: getting latest message for room {room_id} - {e}")
            return None
