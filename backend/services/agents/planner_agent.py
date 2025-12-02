from agents.sub_agents.opening_hours_agent import OpeningHoursAgent
from agents.sub_agents.budget_check_agent import BudgetCheckAgent
from agents.sub_agents.daily_calculation_agent import DailyCalculationAgent
from agents.sub_agents.plan_validator_agent import PlanValidatorAgent
from integration.text_generator_api import TextGeneratorAPI
from services.plan_service import PlanService

class PlannerAgent:
    def __init__(self):
        self.model = TextGeneratorAPI()
        self.plan_service = PlanService()
    
    async def process_plan(self, db, user_id: int, user_text: str):
        
        plan = await self.plan_service.get_plans_by_user(db, user_id)
        # gọi sub-agents
        warnings, modifications = [], []

        for agent_cls in [
            OpeningHoursAgent,
            BudgetCheckAgent,
            DailyCalculationAgent,
            PlanValidatorAgent
        ]:
            
            #tại sao lại có lệnh run ?
            agent = agent_cls()
            res = await agent.run(plan)
            if not res.get("success", True):
                warnings.append(res.get("message"))
            if "modifications" in res:
                modifications.extend(res["modifications"])

        # build LLM prompt + reply
        reply = await self.model.generate_reply(user_text, plan, warnings, modifications)

        return {"ok": True, "message": reply, "plan": plan, "warnings": warnings, "modifications": modifications}
