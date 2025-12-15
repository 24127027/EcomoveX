from typing import Dict, List
from integration.text_generator_api import TextGeneratorAPI

class LLMPlanEditParser:
    def __init__(self):
        self.text_generator = TextGeneratorAPI()
        
    async def parse(self, user_text: str, plan=None) -> List[Dict]:
        # Build destination context if plan is provided
        dest_context = ""
        if plan and plan.destinations:
            dest_list = "\n".join([
                f"  - ID {dest.id}: {dest.note or 'Unknown'} (order: {dest.order_in_day})"
                for dest in plan.destinations
            ])
            dest_context = f"\n\nCurrent destinations in plan:\n{dest_list}\n"
        
        prompt = f"""
        You are an expert plan editing parser.
        User request: "{user_text}"{dest_context}

        Output a JSON array of modifications.
        
        Rules:
        - action ∈ ["add", "remove", "modify_time", "change_budget"]
        - For "add": include "destination_data" (string, the place name)
        - For "remove": include "destination_id" (integer, use the ID from the current destinations list above)
        - For "modify_time": include "destination_id" (integer) and "fields" (start_time/end_time/day)
        - For "change_budget": include "fields": {{"budget": number}}

        Examples:
        - Add: {{"action": "add", "destination_data": "Đầm Sen Park"}}
        - Remove: {{"action": "remove", "destination_id": 15}}  (use actual ID from list above)
        - Change budget: {{"action": "change_budget", "fields": {{"budget": 150000}}}}

        Only output valid JSON array.
        """

        response = await self.text_generator.generate_json(prompt)
        return response