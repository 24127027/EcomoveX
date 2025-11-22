from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.message import Message, MessageStatus, Sender, MessageType
from models.chatbot.planning import ChatSessionContext

class ChatbotMessageRepository:

    @staticmethod
    async def get_history(db: AsyncSession, session_id: int):
        result = await db.execute(
            select(Message)
            .where(Message.chat_session_id == session_id)
            .order_by(Message.created_at.asc())
        )
        return result.scalars().all()

    @staticmethod
    async def add_message(db: AsyncSession, session_id: int, sender_id: int, content: str, sender: Sender):
        msg = Message(
            sender_id=sender_id,
            chat_session_id=session_id,
            content=content,
            message_type=MessageType.text,
            status=MessageStatus.sent
        )
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg
