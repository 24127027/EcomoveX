from services.message_service import MessageService
from services.plan_service import PlanService
from sqlalchemy.ext.asyncio import AsyncSession
from integration.text_generator_api import create_text_generator_api
from fastapi import HTTPException, status
from repository.message_repository import MessageRepository

class ChatbotService:   
    @staticmethod
    async def process_message(db: AsyncSession, user_id: int, room_id: int, user_text: str):
        try:
            text_generator_api = None
            try:
                text_generator_api = await create_text_generator_api()
                
                # Save user message
                await MessageRepository.create_text_message(db, user_id, room_id, user_text)

                planner_result = await PlanService.handle_intent(db, user_id, room_id, user_text)
                action = planner_result.get("action")
                plan_data = planner_result if action else None

                context = await MessageService.load_context(db, user_id, room_id)

                messages_for_llm = [
                    {"role": "system", "content": "Bạn là trợ lý du lịch thông minh của EcomoveX, chuyên tư vấn về du lịch sinh thái và lập kế hoạch chi tiết."}
                ]
                
                # Get history from context object
                history = context.history if context.history else []
                for msg in history[-10:]:
                    messages_for_llm.append({"role": msg.role, "content": msg.content})
                
                messages_for_llm.append({"role": "user", "content": user_text})

                if context.active_trip:
                    trip_info = f"Người dùng đang có chuyến đi đến {context.active_trip.destination}"
                    messages_for_llm.insert(1, {"role": "system", "content": trip_info})

                bot_reply = await text_generator_api.generate_reply(messages_for_llm)

                # Save bot message (sender_id = 0 for bot)
                await MessageRepository.create_text_message(db, 0, room_id, bot_reply)

                # Update context with new messages
                await MessageService.update_context_with_messages(context, user_text, bot_reply)

                return {
                    "ok": True,
                    "message": bot_reply,
                    "action": action,
                    "plan": plan_data
                }
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error generating reply from LLM: {str(e)}"
                )
            finally:
                if text_generator_api:
                    await text_generator_api.close()
                    
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error processing message: {str(e)}"
                )