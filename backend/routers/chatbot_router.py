from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db
from services.chatbot.llm_service import ChatbotMessageService
from pydantic import BaseModel

router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])

class ChatMessage(BaseModel):
    user_id: int
    session_id: int
    message: str

@router.post("/message")
async def send_message(chat_msg: ChatMessage, db: AsyncSession = Depends(get_db)):
    service = ChatbotMessageService(db)
    result = await service.process_message(chat_msg.user_id, chat_msg.session_id, chat_msg.message)
    return result
