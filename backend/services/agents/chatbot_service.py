from services.agents.plan_edit_agent import PlanEditAgent
from services.agents.planner_agent import PlannerAgent
from services.agents.chit_chat_agent import ChitChatAgent
from utils.nlp.rule_engine import RuleEngine, Intent
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any


class ChatbotService:
    """Service điều phối các agent xử lý tin nhắn."""
    
    def __init__(self):
        self.intent_handler = RuleEngine()

    async def handle_user_message(self, db: AsyncSession, user_id: int, room_id: int, user_text: str) -> Dict[str, Any]:
        """Xử lý tin nhắn và điều hướng đến agent phù hợp."""
        parse_result = self.intent_handler.classify(user_text)
        intent, entities = parse_result.intent, parse_result.entities

        edit_intents = [Intent.ADD, Intent.REMOVE, Intent.MODIFY_TIME, Intent.MODIFY_DAY, Intent.MODIFY_LOCATION, Intent.CHANGE_BUDGET]
        query_intents = [Intent.VIEW_PLAN, Intent.SUGGEST, Intent.GET_WEATHER, Intent.GET_ROUTE, Intent.SEARCH_DESTINATION]

        if intent in edit_intents:
            return await PlanEditAgent(db).edit_plan(user_id, room_id, user_text, intent, entities)
        elif intent in query_intents:
            return await PlannerAgent(db).process_plan(user_id, room_id, user_text)
        else:
            return {"ok": True, "message": await ChitChatAgent().chat(user_text), "intent": "chit_chat"}
