# chatbot_service_demo.py
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from typing import Any, Dict, List

from utils.nlp.rule_engine import RuleEngine, ParseResult
from services.plan_service import PlanService
from services.agents.sub_agents.opening_hours_agent import OpeningHoursAgent
from services.agents.sub_agents.budget_check_agent import BudgetCheckAgent
from services.agents.sub_agents.daily_calculation_agent import DailyCalculationAgent
from services.agents.sub_agents.plan_validator_agent import PlanValidatorAgent
from integration.text_generator_api import TextGeneratorAPI

class ChatbotServiceDemo:
    def __init__(self, text_api: TextGeneratorAPI):
        self.plan_service = PlanService()
        self.text_api = text_api
        self.rule_engine = RuleEngine()
        # Sub-agents (bỏ db)
        self.opening_hours_agent = OpeningHoursAgent(db=None)
        self.budget_check_agent = BudgetCheckAgent(db=None)
        self.daily_calc_agent = DailyCalculationAgent(db=None)
        self.plan_validator_agent = PlanValidatorAgent(db=None)

    async def handle_user_message(self, user_msg: str, plan_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point: xử lý message từ user với plan giả lập
        """
        # 1. Load context giả lập (bỏ qua DB)
        history = []

        # 2. Xử lý intent & action bằng RuleEngine
        parse_result: ParseResult = self.rule_engine.classify(user_msg)
        action = {
            "intent": parse_result.intent,
            "entities": parse_result.entities,
            "confidence": parse_result.confidence
        }

        # 3. Dùng plan JSON trực tiếp
        plan = plan_json

        # 4. Call sub-agents (bỏ db, pass plan JSON)
        sub_agent_results = []
        sub_agent_results.append(await self.opening_hours_agent.process(plan, action.get("intent", "validate")))
        sub_agent_results.append(await self.budget_check_agent.process(plan, action.get("intent", "validate")))
        sub_agent_results.append(await self.daily_calc_agent.process(plan, action.get("intent", "validate")))
        validation_result = await self.plan_validator_agent.process(plan, action.get("intent", "validate"))
        sub_agent_results.append(validation_result)

        # 5. Kiểm tra modifications / warnings từ sub-agents
        warnings = []
        modifications = []
        for r in sub_agent_results:
            if not r.get("success", True):
                warnings.append(r.get("message"))
            if "modifications" in r:
                modifications.extend(r["modifications"])

        # 6. Chuẩn bị messages cho OpenRouter
        messages = self.build_messages(user_msg, history, plan, warnings)

        # 7. Gọi TextGeneratorAPI
        llm_response = await self.text_api.generate_reply(messages)

        # 8. Trả JSON cho frontend
        return {
            "response": llm_response,
            "warnings": warnings,
            "modifications": modifications,
        }

    def build_messages(self, user_msg: str, history: List[Any], plan: Dict[str, Any], warnings: List[str]) -> List[Dict[str, str]]:
        """
        Chuẩn hóa messages list cho OpenRouter / TextGeneratorAPI
        """
        messages = []

        # System instruction + warnings
        system_content = "You are a travel assistant."
        if warnings:
            system_content += "\nWarnings:\n" + "\n".join(warnings)
        messages.append({"role": "system", "content": system_content})

        # History
        for item in history:
            messages.append({"role": item.role, "content": item.content})

        # Current plan info
        messages.append({"role": "system", "content": f"Current plan: {plan}"})

        # User message
        messages.append({"role": "user", "content": user_msg})

        return messages


