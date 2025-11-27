from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, delete, select, func, update
from sqlalchemy.exc import SQLAlchemyError
from models.message import *
from schemas.message_schema import *
from typing import List, Optional, Any, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import selectinload

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
    async def get_file_messages_by_room(db: AsyncSession, room_id: int):
        try:
            result = await db.execute(
                select(Message).where(
                    (Message.room_id == room_id) &
                    (Message.message_type == MessageType.file)
                ).order_by(Message.created_at.desc())
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching file messages for room ID {room_id} - {e}")
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
    async def create_text_message(
        db: AsyncSession, sender_id: int, room_id: int, content: str
    ):
        try:
            new_message = Message(
                sender_id=sender_id,
                room_id=room_id,
                message_type=MessageType.text,
                content=content,
                file_blob_name=None,
                status=MessageStatus.sent
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
                status=MessageStatus.sent
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
    async def update_message_status(
        db: AsyncSession,
        message_id: int,
        new_status: MessageStatus
    ):
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
    async def update_message_content(
        db: AsyncSession,
        message_id: int,
        new_content: str
    ):
        try:
            stmt = (
                update(Message)
                .where(
                    and_(
                        Message.id == message_id,
                    )
                )
                .values(content=new_content, edited_at=func.now())
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
            stmt = (
                delete(Message)
                .where(
                    and_(
                        Message.id == message_id,
                    )
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
    async def create_session(
        db: AsyncSession,
        session_data: ChatSessionCreate
    ) -> Optional[ChatSession]:
        try:
            session = ChatSession(
                user_id=session_data.user_id,
                session_token=session_data.session_token,
                status=session_data.status
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
            return session
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Creating chat session - {e}")
            return None

    @staticmethod
    async def get_session_by_id(
        db: AsyncSession,
        session_id: int,
        include_messages: bool = False,
        include_contexts: bool = False
    ) -> Optional[ChatSession]:
        try:
            query = select(ChatSession).where(ChatSession.id == session_id)
            if include_messages:
                query = query.options(selectinload(ChatSession.messages))
            if include_contexts:
                query = query.options(selectinload(ChatSession.contexts))
            
            result = await db.execute(query)
            return result.scalars().first()
        except SQLAlchemyError as e:
            print(f"ERROR: Getting session by ID {session_id} - {e}")
            return None

    @staticmethod
    async def get_session_by_token(
        db: AsyncSession,
        session_token: str,
        include_contexts: bool = False
    ) -> Optional[ChatSession]:
        try:
            query = select(ChatSession).where(ChatSession.session_token == session_token)
            
            if include_contexts:
                query = query.options(selectinload(ChatSession.contexts))
            
            result = await db.execute(query)
            return result.scalars().first()
        except SQLAlchemyError as e:
            print(f"ERROR: Getting session by token - {e}")
            return None

    @staticmethod
    async def get_user_sessions(
        db: AsyncSession,
        user_id: int,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ChatSession]:
        try:
            query = select(ChatSession).where(ChatSession.user_id == user_id)
            
            if status:
                query = query.where(ChatSession.status == status)
            
            query = query.order_by(ChatSession.last_active_at.desc())
            query = query.limit(limit).offset(offset)
            
            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: Getting user sessions for user {user_id} - {e}")
            return []

    @staticmethod
    async def update_session_status(
        db: AsyncSession,
        session_id: int,
        updated_data: ChatSessionUpdate
    ) -> bool:
        try:
            update_dict = {}
            if updated_data.status is not None:
                update_dict['status'] = updated_data.status
            update_dict['last_active_at'] = func.now()
            
            stmt = (
                update(ChatSession)
                .where(ChatSession.id == session_id)
                .values(**update_dict)
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Updating session status for {session_id} - {e}")
            return False

    @staticmethod
    async def update_last_active(
        db: AsyncSession,
        session_id: int
    ) -> bool:
        try:
            stmt = (
                update(ChatSession)
                .where(ChatSession.id == session_id)
                .values(last_active_at=func.now())
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Updating last active for session {session_id} - {e}")
            return False

    @staticmethod
    async def delete_session(
        db: AsyncSession,
        session_id: int
    ) -> bool:
        try:
            stmt = delete(ChatSession).where(ChatSession.id == session_id)
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Deleting session {session_id} - {e}")
            return False

    @staticmethod
    async def delete_inactive_sessions(
        db: AsyncSession,
        days: int = 30
    ) -> int:
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            stmt = delete(ChatSession).where(ChatSession.last_active_at < cutoff_date)
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Deleting inactive sessions - {e}")
            return 0

    @staticmethod
    async def save_session_context(
        db: AsyncSession,
        context_data: ChatSessionContextCreate
    ) -> Optional[ChatSessionContext]:
        try:
            query = select(ChatSessionContext).where(
                and_(
                    ChatSessionContext.session_id == context_data.session_id,
                    ChatSessionContext.key == context_data.key
                )
            )
            result = await db.execute(query)
            context = result.scalars().first()
            
            if context:
                context.value = context_data.value
                context.updated_at = func.now()
            else:
                context = ChatSessionContext(
                    session_id=context_data.session_id,
                    key=context_data.key,
                    value=context_data.value
                )
                db.add(context)
            
            await db.commit()
            await db.refresh(context)
            return context
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Saving session context for session {context_data.session_id}, key {context_data.key} - {e}")
            return None

    @staticmethod
    async def get_session_context(
        db: AsyncSession,
        session_id: int,
        key: str
    ) -> Optional[Any]:
        try:
            query = select(ChatSessionContext).where(
                and_(
                    ChatSessionContext.session_id == session_id,
                    ChatSessionContext.key == key
                )
            )
            result = await db.execute(query)
            context = result.scalars().first()
            return context.value if context else None
        except SQLAlchemyError as e:
            print(f"ERROR: Getting context for session {session_id}, key {key} - {e}")
            return None

    @staticmethod
    async def load_session_context(
        db: AsyncSession,
        session_id: int
    ) -> Dict[str, Any]:
        try:
            query = select(ChatSessionContext).where(
                ChatSessionContext.session_id == session_id
            )
            result = await db.execute(query)
            contexts = result.scalars().all()
            return {context.key: context.value for context in contexts}
        except SQLAlchemyError as e:
            print(f"ERROR: Loading session context for session {session_id} - {e}")
            return {}

    @staticmethod
    async def delete_session_context(
        db: AsyncSession,
        session_id: int,
        key: str
    ) -> bool:
        try:
            stmt = delete(ChatSessionContext).where(
                and_(
                    ChatSessionContext.session_id == session_id,
                    ChatSessionContext.key == key
                )
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Deleting context for session {session_id}, key {key} - {e}")
            return False

    @staticmethod
    async def clear_session_context(
        db: AsyncSession,
        session_id: int
    ) -> bool:
        try:
            stmt = delete(ChatSessionContext).where(
                ChatSessionContext.session_id == session_id
            )
            await db.execute(stmt)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: Clearing context for session {session_id} - {e}")
            return False

    @staticmethod
    async def search_sessions(
        db: AsyncSession,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ChatSession]:
        try:
            query = select(ChatSession)
            
            conditions = []
            if user_id:
                conditions.append(ChatSession.user_id == user_id)
            if status:
                conditions.append(ChatSession.status == status)
            if from_date:
                conditions.append(ChatSession.created_at >= from_date)
            if to_date:
                conditions.append(ChatSession.created_at <= to_date)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.order_by(ChatSession.created_at.desc())
            query = query.limit(limit).offset(offset)
            
            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: Searching sessions - {e}")
            return []
    
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