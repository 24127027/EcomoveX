# services/chat_service.py
from repository.chatbot_message_repository import ChatbotMessageRepository
from services.chatbot.context_manager import ContextManager
from services.chatbot.planner_handle import PlannerHandler
import httpx
import os
from sqlalchemy.ext.asyncio import AsyncSession

OPEN_ROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")
# Updated to use working free model
OPEN_ROUTER_MODEL = os.getenv("OPEN_ROUTER_MODEL", "google/gemma-2-27b-it") 

class LLMService:
    """Service to send messages to Open Router"""
    def __init__(self, api_key: str = OPEN_ROUTER_API_KEY, model: str = OPEN_ROUTER_MODEL):
        self.api_key = api_key
        #meta-llama/llama-3.3-70b-instruct or google/gemma-2-27b-it 
        self.model = "meta-llama/llama-3.3-70b-instruct"
        self.url = "https://openrouter.ai/api/v1/chat/completions"


    async def generate_reply(self, context_messages: list):
        """
        context_messages: list of dicts with 'role' and 'content', e.g.
            [{"role": "user", "content": "Hi"}]
        """
        headers = {
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json",
        "X-Title": "EcomoveX",
        "Referer": "http://localhost:3000",
        "Origin": "http://localhost:3000"
        }
        payload = {
            "model": self.model,
            "messages": context_messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    self.url, 
                    json=payload, 
                    headers=headers
                )
                
                # Debug: Print response details
                # print(f"LLM Status Code: {resp.status_code}")
                # print("LLM RAW RESPONSE:", resp.text[:300])  # 👈 IMPORTANT

                # print(f"LLM Status Code: {resp.status_code}")
                # print("LLM RAW RESPONSE:", resp.text[:300])  # 👈 IMPORTANT

                resp.raise_for_status()

                # Handle empty or invalid JSON
                if not resp.text or resp.text.strip() == "":
                    raise Exception("❌ Empty response from LLM (status 200 but body is empty)")

                # Try parse JSON safely
                try:
                    data = resp.json()
                except Exception as json_err:
                    print("❌ JSON PARSE ERROR. RAW body returned by LLM:")
                    print(resp.text)
                    raise Exception("LLM returned non-JSON body") from json_err

                # Validate format
                if "choices" not in data or len(data["choices"]) == 0:
                    print("❌ Invalid LLM response structure:")
                    print(data)
                    raise Exception("Invalid response format: missing 'choices'")

                # Extract reply
                reply = data["choices"][0]["message"]["content"]
                return reply
                
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e}")
            print(f"Response: {e.response.text}")
            raise
        except Exception as e:
            print(f"Error: {e}")
            raise

class ChatbotMessageService:
    """Service to handle user message -> LLM reply"""
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ChatbotMessageRepository()
        self.context_mgr = ContextManager(db)
        self.planner = PlannerHandler(db)
        self.llm = LLMService()

    async def process_message(self, user_id: int, session_id: int, user_text: str):
        # 1 Save user message
        await self.repo.add_message(self.db, session_id, user_id, user_text, sender="user")

        # 2 Planner handler (check if it's ADD/REMOVE/MODIFY intent)
        planner_result = await self.planner.handle(user_id, session_id, user_text)
        action = planner_result.get("action")
        plan_data = planner_result if action else None

        # 3 Load context
        context = await self.context_mgr.load_context(user_id, session_id)

        # Add latest user message to context for LLM
        messages_for_llm = [
            {"role": "system", "content": "Bạn là trợ lý du lịch thông minh của EcomoveX, chuyên tư vấn về du lịch sinh thái và lập kế hoạch chi tiết."}
        ]
        
        # Include last 10 messages from history (simplified)
        history = context.get("history", [])
        for msg in history[-10:]:
            messages_for_llm.append({"role": "user", "content": str(msg)})
        
        # Include latest message
        messages_for_llm.append({"role": "user", "content": user_text})

        # Optional: add active trip info
        if context.get("active_trip"):
            trip_info = f"Người dùng đang có chuyến đi đến {context['active_trip'].destination}"
            messages_for_llm.insert(1, {"role": "system", "content": trip_info})

        # 4 Call LLM
        bot_reply = await self.llm.generate_reply(messages_for_llm)

        # 5 Save bot reply
        await self.repo.add_message(self.db, session_id, user_id, bot_reply, sender="bot")

        # 6 Update short-term context
        await self.context_mgr.update_context(context, user_text, bot_reply)

        return {
            "ok": True,
            "message": bot_reply,
            "action": action,
            "plan": plan_data
        }