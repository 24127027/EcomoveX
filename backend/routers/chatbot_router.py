from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db
from services.chatbot_service import ChatbotService
from schemas.message_schema import ChatMessage
from typing import Dict, Any

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

@router.post("/message", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def send_message(chat_msg: ChatMessage, db: AsyncSession = Depends(get_db)):
    result = await ChatbotService.process_message(db, chat_msg.user_id, chat_msg.room_id, chat_msg.message)
    return result
