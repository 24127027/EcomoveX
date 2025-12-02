from agents.plan_edit_agent import PlanEditAgent
from agents.planner_agent import PlannerAgent
from agents.chit_chat_agent import ChitChatAgent
from utils.nlp.rule_engine import RuleEngine

class ChatbotService:
    async def handle_user_message(self, db, user_id: int, room_id: int, user_text: str):
        self.intent_handler = RuleEngine()
        
        intent = await self.intent_handler.classify(user_text)

        if intent == "plan_edit":
            # user muốn sửa trực tiếp plan
            result = await PlanEditAgent().edit_plan(db, user_id, user_text)
        elif intent == "plan_query":
            # plan-related, gọi PlannerAgent
            result = await PlannerAgent().process_plan(db, user_id, user_text)
        else:
            # chỉ chat bình thường
            reply = await ChitChatAgent().chat(user_text)
            result = {"ok": True, "message": reply}

        return result
