"""
PlanEditAgent - Chatbot Plan Editing Service

ARCHITECTURE:
This agent processes plan edit requests from the chatbot and returns suggested modifications
WITHOUT saving to the database. The correct flow is:

1. Chatbot receives user request (e.g., "add Eiffel Tower")
2. PlanEditAgent parses the request and generates modified plan structure
3. Frontend receives the suggestions and updates local state
4. User reviews the changes in the UI
5. User explicitly clicks "Save Plan" → ONLY THEN database is updated

This ensures:
- Chatbot operates as a suggestion/preview system
- Users maintain control over what gets saved
- No unwanted database mutations during chat operations
"""

from services.agents.planner_agent import PlannerAgent
from services.plan_service import PlanService
from utils.nlp.llm_plan_edit_parser import LLMPlanEditParser
from typing import List, Dict

class PlanEditAgent:
    def __init__(self):
        self.plan_service = PlanService()
        self.llm_parser = LLMPlanEditParser()

    async def apply_modifications_to_plan_structure(self, plan, modifications: List[Dict]):
        """
        Apply modifications to the plan structure WITHOUT saving to database.
        Returns the modified plan structure for frontend to handle.
        """
        # Create a copy of the plan data to avoid modifying the original
        modified_plan = {
            "place_name": plan.place_name,
            "start_date": str(plan.start_date),  # ✅ Correct field name
            "end_date": str(plan.end_date),      # ✅ Correct field name
            "budget_limit": plan.budget_limit or 0,
            "destinations": []
        }
        
        # Convert existing destinations to dict format
        destinations = []
        for dest in plan.destinations:  # ✅ Correct field name
            destinations.append({
                "destination_id": str(dest.destination_id),  # ✅ Correct field
                "destination_type": dest.type,  # ✅ Already correct type
                "visit_date": str(dest.visit_date),  # ✅ Correct field
                "order_in_day": dest.order_in_day,
                "time_slot": dest.time_slot.value if hasattr(dest.time_slot, 'value') else str(dest.time_slot).lower(),
                "note": dest.note or "",
                "address": "",  # Not available in PlanDestinationResponse
                "url": dest.url or "",
                "estimated_cost": dest.estimated_cost or 0
            })
        
        # Apply modifications
        for mod in modifications:
            action = mod.get("action")
            
            if action == "add":
                # Add new destination to the list
                dest_data = mod.get("destination_data")
                dest_name = dest_data.get("name") if isinstance(dest_data, dict) else dest_data
                
                new_dest = {
                    "destination_id": f"new-{len(destinations)}",
                    "destination_type": "attraction",
                    "visit_date": str(plan.start_date),  # ✅ Use start_date
                    "order_in_day": len(destinations) + 1,
                    "time_slot": "morning",
                    "note": dest_name,
                    "address": "",
                    "url": "",
                    "estimated_cost": 0
                }
                destinations.append(new_dest)
                print(f"➕ Added destination suggestion: {dest_name}")
                
            elif action == "remove":
                # Remove destination from the list
                dest_data = mod.get("destination_id")
                dest_id = str(dest_data.get("id") if isinstance(dest_data, dict) else dest_data)
                destinations = [d for d in destinations if str(d["destination_id"]) != dest_id]
                print(f"➖ Removed destination suggestion: {dest_id}")
                
            elif action == "change_budget":
                # Update budget in plan structure
                budget_value = mod["fields"].get("budget")
                if budget_value:
                    modified_plan["budget_limit"] = float(budget_value)
                    print(f"💰 Updated budget suggestion: {budget_value}")
        
        modified_plan["destinations"] = destinations
        return modified_plan



    async def edit_plan(self, db, user_id: int, user_text: str):
        """
        Process plan edit request and return modified plan structure WITHOUT saving to database.
        Frontend will handle state updates and user explicitly saves later.
        """
        self.plan_service = PlanService()
        
        # Get user's plans
        all_plans = await self.plan_service.get_plans_by_user(db, user_id)
        
        # Check if user has any plans
        if not all_plans.plans or len(all_plans.plans) == 0:
            return {
                "success": False,
                "message": "You don't have any plans yet. Please create a plan first.",
                "plan": None
            }
        
        # Get the latest plan (assuming the last one is the most recent)
        # TODO: In the future, we should let users specify which plan to edit
        latest_plan_basic = all_plans.plans[-1]
        
        # Get full plan details
        plan = await self.plan_service.get_plan_by_id(db, user_id, latest_plan_basic.id)
        
        # Parse user_text to identify modifications (pass plan for context)
        modifications = await self.llm_parser.parse(user_text, plan)
        
        print(f"📝 Generating plan suggestions (NOT saving to database):")
        print(f"   - Modifications: {len(modifications)}")
        for mod in modifications:
            print(f"   - {mod.get('action')}: {mod}")
        
        # Apply modifications to plan structure (returns modified copy, does NOT save)
        modified_plan = await self.apply_modifications_to_plan_structure(plan, modifications)
        
        # Generate response message
        action_messages = []
        for mod in modifications:
            action = mod.get("action")
            if action == "add":
                dest_data = mod.get("destination_data")
                dest_name = dest_data.get("name") if isinstance(dest_data, dict) else dest_data
                action_messages.append(f"Added {dest_name}")
            elif action == "remove":
                action_messages.append("Removed a destination")
            elif action == "change_budget":
                budget_value = mod["fields"].get("budget")
                action_messages.append(f"Updated budget to {budget_value}")
        
        message = f"I've suggested changes to your plan '{plan.place_name}': " + ", ".join(action_messages) if action_messages else f"Here are my suggestions for your plan '{plan.place_name}'"
        
        return {
            "success": True,
            "message": message,
            "plan": modified_plan
        }
