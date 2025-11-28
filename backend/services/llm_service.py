from repository.message_repository import MessageRepository
from services.message_service import MessageService
from services.plan_service import PlanService
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from utils.config import settings

class LLMService:
    
    @staticmethod
    async def generate_reply(context_messages: list, api_key: str = settings.OPEN_ROUTER_API_KEY, model: str = settings.OPEN_ROUTER_MODEL_NAME) -> str:
        if model is None:
            model = "meta-llama/llama-3.3-70b-instruct"
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Title": "EcomoveX",
            "Referer": "http://localhost:3000",
            "Origin": "http://localhost:3000"
        }
        
        payload = {
            "model": model,
            "messages": context_messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()

                if not resp.text or resp.text.strip() == "":
                    raise Exception("Empty response from LLM")

                try:
                    data = resp.json()
                except Exception as json_err:
                    raise Exception("LLM returned non-JSON body") from json_err

                if "choices" not in data or len(data["choices"]) == 0:
                    raise Exception("Invalid response format: missing 'choices'")

                reply = data["choices"][0]["message"]["content"]
                return reply
                
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP Error: {e.response.text}")
        except Exception as e:
            raise Exception(f"LLM Error: {str(e)}")

class ChatbotMessageService:
    
    @staticmethod
    async def process_message(db: AsyncSession, user_id: int, session_id: int, user_text: str):
        try:
            await MessageRepository.add_message(db, session_id, user_id, user_text, sender="user")

            planner_result = await PlanService.handle_intent(db, user_id, session_id, user_text)
            action = planner_result.get("action")
            plan_data = planner_result if action else None

            context = await MessageService.load_context(db, user_id, session_id)

            messages_for_llm = [
                {"role": "system", "content": "Bạn là trợ lý du lịch thông minh của EcomoveX, chuyên tư vấn về du lịch sinh thái và lập kế hoạch chi tiết."}
            ]
            
            history = context.get("history", [])
            for msg in history[-10:]:
                messages_for_llm.append({"role": "user", "content": str(msg)})
            
            messages_for_llm.append({"role": "user", "content": user_text})

            if context.get("active_trip"):
                trip_info = f"Người dùng đang có chuyến đi đến {context['active_trip'].destination}"
                messages_for_llm.insert(1, {"role": "system", "content": trip_info})

            bot_reply = await LLMService.generate_reply(messages_for_llm)

            await MessageRepository.add_message(db, session_id, user_id, bot_reply, sender="bot")

            await MessageService.update_context(db, context, user_text, bot_reply)

            return {
                "ok": True,
                "message": bot_reply,
                "action": action,
                "plan": plan_data
            }
            
        except Exception as e:
            raise Exception(f"Error processing message: {str(e)}")