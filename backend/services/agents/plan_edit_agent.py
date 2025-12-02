from agents.planner_agent import PlannerAgent
from services.plan_service import PlanService
from typing import List, Dict

class PlanEditAgent:
    def __init__(self):
        self.plan_service = PlanService()

    async def apply_modifications(self, db, plan, modifications: List[Dict], user_id: int):
        for mod in modifications:
            action = mod.get("action")
            if action == "add_destination":
                await PlanService.add_destination_to_plan(db, user_id, plan.id, mod["destination_data"])
            elif action == "remove_destination":
                await PlanService.remove_destination_from_plan(db, user_id, plan.id, mod["destination_id"])
            elif action == "update_destination":
                await PlanService.update_destination(db, user_id, plan.id, mod["destination_id"], mod["fields"])
            elif action == "update_plan":
                await PlanService.update_plan_info(db, user_id, plan.id, mod["fields"])

    #=============================================================================#
    # Thêm mấy hàm xử lý update plan info
    
    
    #=============================================================================#
    
    
    async def edit_plan(self, db, user_id: int, user_text: str):
        self.plan_service = PlanService()
        # parse user_text để xác định thay đổi
        plan = await self.plan_service.get_plans_by_user(db, user_id)

        # thực hiện update DB
        await self.apply_modifications(db, plan, user_text, user_id)
        # validate lại plan
        plan = await PlannerAgent().process_plan(db, user_id, "validate after edit")
        return plan
