from services.agents.sub_agents.opening_hours_agent import OpeningHoursAgent
from services.agents.sub_agents.budget_check_agent import BudgetCheckAgent
from services.agents.sub_agents.daily_calculation_agent import DailyCalculationAgent
from services.agents.sub_agents.plan_validator_agent import PlanValidatorAgent
from integration.text_generator_api import TextGeneratorAPI
from services.plan_service import PlanService
from pathlib import Path

class PlannerAgent:
    def __init__(self):
        self.model = TextGeneratorAPI()
        self.plan_service = PlanService()
        instruction_path = Path(__file__).parent.parent / "instructions" / "main_agent.txt"
        self.instruction = self.load_instruction(str(instruction_path))
    
    def load_instruction(self, filepath: str) -> str:
        """
        Load instruction text from a file.

        Args:
            filepath (str): Path tới file instruction (.txt)

        Returns:
            str: Nội dung file dưới dạng string
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Instruction file not found: {filepath}")
        
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        
        return content
    
    async def process_plan(self, db, user_id: int, user_text: str):
        plan = await self.plan_service.get_plans_by_user(db, user_id)
        warnings, modifications = [], []

        for agent_cls in [
            OpeningHoursAgent,
            BudgetCheckAgent,
            DailyCalculationAgent,
            PlanValidatorAgent
        ]:
            agent = agent_cls()
            res = await agent.process(plan)
            
            if not res.get("success", True):
                warnings.append(res.get("message"))
            if "modifications" in res:
                modifications.extend(res["modifications"])
        
        context_messages = [
            {"role": "system", "content": self.instruction},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": f"Current plan: {plan}"},
            {"role": "assistant", "content": f"Warnings: {warnings}"},
            {"role": "assistant", "content": f"Modifications: {modifications}"},
        ]

        reply = await self.model.generate_reply(context_messages)

        return {"ok": True, "message": reply, "plan": plan, "warnings": warnings, "modifications": modifications}
