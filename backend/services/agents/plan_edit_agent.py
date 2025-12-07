from services.agents.planner_agent import PlannerAgent
from services.plan_service import PlanService
from utils.nlp.llm_plan_edit_parser import LLMPlanEditParser
from typing import List, Dict

class PlanEditAgent:
    def __init__(self):
        self.plan_service = PlanService()
        self.llm_parser = LLMPlanEditParser()

    async def apply_modifications(self, db, plan, modifications: List[Dict], user_id: int):
        for mod in modifications:
            action = mod.get("action")
            if action == "add":
                await PlanService.add_place_by_text(db, user_id, plan.id, mod["destination_data"])
            elif action == "remove":
                await PlanService.remove_place_by_name(db, user_id, plan.id, mod["destination_id"])
            elif action == "modify_time":
                await PlanService.update_destination_time(db, user_id, plan.id, mod["destination_id"], mod["fields"])
            elif action == "change_budget":
                await PlanService.update_budget(db, user_id, plan.id, mod["fields"])


    async def edit_plan(self, db, user_id: int, user_text: str):
        self.plan_service = PlanService()
        # parse user_text để xác định thay đổi
        plan = await self.plan_service.get_plans_by_user(db, user_id)
        
        modifications = await self.llm_parser.parse(user_text)
        
        # thực hiện update DB
        await self.apply_modifications(db, plan, modifications, user_id)
        # validate lại plan
        plan = await PlannerAgent().process_plan(db, user_id, "validate after edit")
        return plan
