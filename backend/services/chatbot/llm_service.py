# services/chat_service.py
from repository.chatbot_message_repository import ChatbotMessageRepository
from services.chatbot.context_manager import ContextManager
from services.chatbot.planner_handle import PlannerHandler
import httpx
import os
from sqlalchemy.ext.asyncio import AsyncSession

OPEN_ROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")
OPEN_ROUTER_MODEL = os.getenv("OPEN_ROUTER_MODEL", "gpt-4.1-mini")  # example

class LLMService:
    """Service to send messages to Open Router"""
    def __init__(self, api_key: str = OPEN_ROUTER_API_KEY, model: str = OPEN_ROUTER_MODEL):
        self.api_key = api_key
        self.model = model
        self.url = f"https://openrouter.ai/api/v1/chat/completions"

    async def generate_reply(self, context_messages: list):
        """
        context_messages: list of dicts with 'role' and 'content', e.g.
            [{"role": "user", "content": "Hi"}]
        """
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": context_messages,
            "temperature": 0.7
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            # Open Router returns content in data['choices'][0]['message']['content']
            reply = data["choices"][0]["message"]["content"]
            return reply

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
        messages_for_llm = [{"role": "system", "content": "Bạn là trợ lý du lịch thông minh."}]
        # Include last 20 messages
        messages_for_llm.extend([{"role": "user", "content": m} for m in context["history"]])
        # Include latest message
        messages_for_llm.append({"role": "user", "content": user_text})

        # Optional: add active trip info
        if context.get("active_trip"):
            messages_for_llm.append({"role": "system", "content": f"Active trip: {context['active_trip'].title}"})

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
