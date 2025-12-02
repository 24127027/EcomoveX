from typing import Any, Dict

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from schemas.message_schema import ChatMessage
from services.chatbot_service import ChatbotService

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


@router.post("/message", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def send_message(chat_msg: ChatMessage, db: AsyncSession = Depends(get_db)):
    result = await ChatbotService.process_message(
        db, chat_msg.user_id, chat_msg.room_id, chat_msg.message
    )
    return result


@router.post(
    "/verify-green", response_model=Dict[str, Any], status_code=status.HTTP_200_OK
)
async def verify_green_transportation(
    data: Dict[str, Any], db: AsyncSession = Depends(get_db)
):
    """
    Verify green transportation method usage.

    Request body:
    {
        "user_id": 1,
        "transportation_type": "bicycle",  // bicycle, walking, electric_vehicle, public_transport
        "image_url": "https://...",        // optional proof image
        "location": {                       // optional GPS verification
            "lat": 10.762622,
            "lng": 106.660172
        },
        "timestamp": "2025-11-28T10:30:00"
    }
    """
    return {"error": "This endpoint is not yet implemented"}
