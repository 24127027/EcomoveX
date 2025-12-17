from services.agents.plan_edit_agent import PlanEditAgent
from services.agents.planner_agent import PlannerAgent
from services.agents.chit_chat_agent import ChitChatAgent
from utils.nlp.rule_engine import RuleEngine
from utils.nlp.llm_intent_parser import LLMIntentParser
from schemas.message_schema import ChatbotResponse

class ChatbotService:
    async def detect_intent(self, user_text: str) -> str:
        self.intent_rule = RuleEngine()
        self.intent_llm  = LLMIntentParser()

        # Sử dụng LLM trước, fall back về rule-based nếu LLM fails
        try:
            intent = await self.intent_llm.parse(user_text)
            if intent and intent != "unknown":
                return intent
        except Exception:
            pass
        
        try:
            result = self.intent_rule.classify(user_text)
            # Extract intent string from ParseResult object
            if hasattr(result, 'intent'):
                return result.intent
            return result
        except Exception:
            return "chit_chat"
    
    async def handle_user_message(self, db, user_id: int, room_id: int, user_text: str, current_plan: dict = None) -> ChatbotResponse:
        """
        Normalize all output to ChatbotResponse.
        """
        intent = await self.detect_intent(user_text)
        
        print(f"🎯 Detected intent: {intent}")

        # Map rule-based intents to agent types
        # Plan edit intents: add, remove, modify, change_budget
        plan_edit_intents = [
            "add_activity",
            "remove_activity", 
            "modify_time",
            "modify_day",
            "modify_location",
            "change_budget"
        ]
        
        # Plan query intents: view, search
        plan_query_intents = [
            "view_plan",
            "search_destination",
            "suggest_alternative"
        ]

        # plan edit
        if intent in plan_edit_intents or intent == "plan_edit":
            result = await PlanEditAgent().edit_plan(db, user_id, user_text, current_plan)

            return ChatbotResponse(
                response=result.get("message", "Plan updated."),
                room_id=room_id,
                metadata={
                    "intent": intent,
                    "raw": result
                }
            )

        # plan query/planning
        elif intent in plan_query_intents or intent == "plan_query":
            result = await PlannerAgent().process_plan(db, user_id, user_text)

            return ChatbotResponse(
                response=result.get("message", "Here is your plan."),
                room_id=room_id,
                metadata={
                    "intent": intent,
                    "raw": result
                }
            )

        # chatchit
        else:
            reply = await ChitChatAgent().chat(user_text)

            return ChatbotResponse(
                response=reply,
                room_id=room_id,
                metadata={
                    "intent": "chit_chat"
                }
            )