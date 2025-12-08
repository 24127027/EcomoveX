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
                # Extract destination name from dict or use as-is if string
                dest_data = mod.get("destination_data")
                dest_name = dest_data.get("name") if isinstance(dest_data, dict) else dest_data
                await PlanService.add_place_by_text(db, user_id, plan.id, dest_name)
            elif action == "remove":
                # Extract destination id from dict or use as-is if integer
                dest_data = mod.get("destination_id")
                dest_id = dest_data.get("id") if isinstance(dest_data, dict) else dest_data
                await PlanService.remove_place_by_id(db, user_id, plan.id, int(dest_id))
            # Cho thêm điểm thì phát triển sau
            # elif action == "modify_time":
            #     # Extract time modifications from fields dict
            #     await PlanService.update_destination_time(db, user_id, plan.id, mod["destination_id"], mod["fields"])
            elif action == "change_budget":
                # Extract budget value from fields dict
                budget_value = mod["fields"].get("budget")
                print(type(budget_value))
                if budget_value:
                    await PlanService.update_budget(db, user_id, plan.id, float(budget_value))



    async def edit_plan(self, db, user_id: int, user_text: str):
        self.plan_service = PlanService()
        
        # Get user's plans
        all_plans = await self.plan_service.get_plans_by_user(db, user_id)
        
        # Check if user has any plans
        if not all_plans.plans or len(all_plans.plans) == 0:
            return {
                "success": False,
                "message": "You don't have any plans yet. Please create a plan first."
            }
        
        # Get the latest plan (assuming the last one is the most recent)
        # TODO: In the future, we should let users specify which plan to edit
        latest_plan_basic = all_plans.plans[-1]
        
        # Get full plan details
        plan = await self.plan_service.get_plan_by_id(db, user_id, latest_plan_basic.id)
        
        # Parse user_text to identify modifications (pass plan for context)
        modifications = await self.llm_parser.parse(user_text, plan)
        
        # Apply modifications to the database
        await self.apply_modifications(db, plan, modifications, user_id)
        
        # Validate plan after edit (pass plan_id to ensure we validate the same plan)
        planner_agent = PlannerAgent(db)
        validation_result = await planner_agent.process_plan(user_id, user_text, action="validate", plan_id=plan.id)
        
        return {
            "success": True,
            "message": f"Successfully updated your plan '{plan.place_name}'",
            "plan": validation_result
        }
