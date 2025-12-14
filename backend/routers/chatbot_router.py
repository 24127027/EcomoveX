from fastapi import APIRouter
from schemas.chatbot_schema import ChatMessage
from services.chatbot_service import ChatbotService

router = APIRouter()
chatbot_service = ChatbotService()

@router.post("/chatbot/message")
async def chat_message(data: ChatMessage):
    reply = await chatbot_service.handle_user_message(data)

    return {
        "response": reply
    }
