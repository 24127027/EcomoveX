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

from services.plan_service import PlanService
from utils.nlp.llm_plan_edit_parser import LLMPlanEditParser
from integration.map_api import MapAPI
from schemas.map_schema import TextSearchRequest
from typing import List, Dict

class PlanEditAgent:
    def __init__(self):
        self.plan_service = PlanService()
        self.llm_parser = LLMPlanEditParser()
        self.map_api = MapAPI()

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

        # ✅ Deduplicate EXISTING destinations from database (in case DB has duplicates)
        seen = set()
        deduplicated_existing = []
        for dest in destinations:
            key = f"{dest['destination_id']}_{dest['visit_date']}_{dest['time_slot']}"
            if key not in seen:
                seen.add(key)
                deduplicated_existing.append(dest)
            else:
                print(f"🗑️ Removed existing duplicate from DB: {dest['note']} on {dest['visit_date']} ({dest['time_slot']})")

        destinations = deduplicated_existing
        print(f"✅ Loaded {len(destinations)} unique destinations from database")

        # Apply modifications
        for mod in modifications:
            action = mod.get("action")

            if action == "add":
                # Add new destination to the list
                dest_data = mod.get("destination_data")
                dest_name = dest_data.get("name") if isinstance(dest_data, dict) else dest_data

                # ✅ Search Google Places API to get real place details
                try:
                    search_request = TextSearchRequest(query=dest_name)
                    search_result = await self.map_api.text_search_place(search_request, convert_photo_urls=True)

                    if search_result.places and len(search_result.places) > 0:
                        place = search_result.places[0]  # Get first result
                        
                        # Only add destination if we have a valid place_id
                        if place.place_id and is_valid_place_id(place.place_id):
                            new_dest = {
                                "destination_id": place.place_id,  # ✅ Real Google Place ID
                                "destination_type": place.types[0] if place.types else "attraction",
                                "visit_date": str(plan.start_date),
                                "order_in_day": len(destinations) + 1,
                                "time_slot": "morning",
                                "note": place.name,
                                "address": place.formatted_address or "",
                                "url": place.photos.photo_url if place.photos and place.photos.photo_url else "",
                                "estimated_cost": 0
                            }
                            destinations.append(new_dest)
                            print(f"✅ Found and added place: {place.name} (ID: {place.place_id})")
                        else:
                            print(f"⚠️ Invalid place_id returned for '{dest_name}', skipping")
                    else:
                        # No results found - skip this destination
                        print(f"⚠️ No results found for '{dest_name}', skipping destination")
                except Exception as e:
                    print(f"❌ Error searching for place '{dest_name}': {str(e)}, skipping destination")

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



    async def edit_plan(self, db, user_id: int, user_text: str, current_plan_data: dict = None):
        """
        Process plan edit request and return modified plan structure WITHOUT saving to database.
        Frontend will handle state updates and user explicitly saves later.
        
        Args:
            current_plan_data: Optional dict with current plan state from frontend
                             If provided, uses this instead of fetching from database
        """
        self.plan_service = PlanService()

        # If frontend provides current plan state, use it directly
        if current_plan_data:
            print("📦 Using current plan data from frontend (unsaved changes)")
            # Convert dict to object-like structure for compatibility
            class PlanData:
                def __init__(self, data):
                    self.place_name = data.get("place_name") or data.get("name")
                    self.start_date = data.get("start_date") or data.get("date")
                    self.end_date = data.get("end_date")
                    self.budget_limit = data.get("budget_limit") or data.get("budget")
                    self.destinations = []

                    # Convert destinations
                    for dest in data.get("destinations", []):
                        class Dest:
                            def __init__(self, d):
                                self.id = d.get("id") or d.get("destination_id")  # ✅ Add id for parser
                                self.destination_id = d.get("destination_id") or d.get("id")
                                self.type = d.get("destination_type") or d.get("type")
                                self.visit_date = d.get("visit_date") or d.get("date")
                                self.order_in_day = d.get("order_in_day")
                                self.time_slot = d.get("time_slot")
                                self.note = d.get("note") or d.get("title")
                                self.url = d.get("url") or d.get("image_url")
                                self.estimated_cost = d.get("estimated_cost") or 0
                        self.destinations.append(Dest(dest))

            plan = PlanData(current_plan_data)
        else:
            # Fallback: Get from database if no current data provided
            print("📡 Fetching plan from database (no current state provided)")
            all_plans = await self.plan_service.get_plans_by_user(db, user_id)

            # Check if user has any plans
            if not all_plans.plans or len(all_plans.plans) == 0:
                return {
                    "success": False,
                    "message": "You don't have any plans yet. Please create a plan first.",
                    "plan": None
                }

            # Get the latest plan
            latest_plan_basic = all_plans.plans[-1]
            plan = await self.plan_service.get_plan_by_id(db, user_id, latest_plan_basic.id)

        # Parse user_text to identify modifications (pass plan for context)
        modifications = await self.llm_parser.parse(user_text, plan)

        print("📝 Generating plan suggestions (NOT saving to database):")
        print(f"   - Modifications: {len(modifications)}")
        for mod in modifications:
            print(f"   - {mod.get('action')}: {mod}")

        # Apply modifications to plan structure (returns modified copy, does NOT save)
        modified_plan = await self.apply_modifications_to_plan_structure(plan, modifications)

        # Note: Deduplication already done in apply_modifications_to_plan_structure
        print(f"✅ Final plan has {len(modified_plan['destinations'])} destinations")

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
