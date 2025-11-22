from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from database.db import get_db
from services.chatbot.planner_handle import PlannerHandler
from services.chatbot.context_manager import ContextManager

router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])

class ChatMessage(BaseModel):
    user_id: int
    session_id: int
    message: str

class ChatResponse(BaseModel):
    ok: bool
    message: str = None
    action: str = None
    data: dict = None

@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_msg: ChatMessage,
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message to the chatbot and receive a response
    """
    try:
        # Initialize planner handler
        planner = PlannerHandler(db)
        
        # Process the message
        result = await planner.handle(
            user_id=chat_msg.user_id,
            session_id=chat_msg.session_id,
            user_text=chat_msg.message
        )
        
        return ChatResponse(
            ok=result.get("ok", False),
            message=result.get("message"),
            action=result.get("action"),
            data=result
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get chat history for a session
    """
    context_mgr = ContextManager(db)
    context = await context_mgr.load_context(user_id, session_id)
    
    return {
        "ok": True,
        "history": context.get("history", []),
        "active_trip": context.get("active_trip")
    }