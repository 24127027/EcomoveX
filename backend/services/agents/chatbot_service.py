from agents.plan_edit_agent import PlanEditAgent
from agents.planner_agent import PlannerAgent
from agents.chit_chat_agent import ChitChatAgent
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
            intent = self.intent_rule.classify(user_text)
        except Exception:
            return "chit_chat"
        
        
        async def handle_user_message(self, db, user_id: int, room_id: int, user_text: str) -> ChatbotResponse:
            """
            Normalize all output to ChatbotResponse.
            """
            intent = await self.detect_intent(user_text)

            # plan edit
            if intent == "plan_edit":
                result = await PlanEditAgent().edit_plan(db, user_id, user_text)

                return ChatbotResponse(
                    response=result.get("message", "Plan updated."),
                    room_id=room_id,
                    metadata={
                        "intent": "plan_edit",
                        "raw": result
                    }
                )

            # plan query/planning
            elif intent == "plan_query":
                result = await PlannerAgent().process_plan(db, user_id, user_text)

                return ChatbotResponse(
                    response=result.get("message", "Here is your plan."),
                    room_id=room_id,
                    metadata={
                        "intent": "plan_query",
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
            
        
                
