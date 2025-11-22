# api/chatbot.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from services.chatbot.planner_handle import PlannerHandler
from repository.plan_repository import load_session_context
from database.db import get_db
from utils.token.authentication_util import get_current_user

router = APIRouter()

@router.post("/chatbot/message")
async def chatbot_message(payload: dict, db: AsyncSession = Depends(get_db), user=Depends(get_current_user), session=Depends(load_session_context)):
    text = payload.get("message")
    # first stage: rule-based / intent
    handler = PlannerHandler(db)
    result = await handler.handle(user.id, session.id, text)
    # Save interaction to messages: reuse MessageRepository.create_message (sender user + session)
    # Then pass to LLM if fallback or for richer response generation
    return result
