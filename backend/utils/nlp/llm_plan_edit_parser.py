from typing import Dict, List
from integration.text_generator_api import TextGeneratorAPI

class LLMPlanEditParser:
    def __init__(self):
        self.text_generator = TextGeneratorAPI()
        
    async def parse(self, user_text: str) -> List[Dict]:
        prompt = f"""
        You are an expert plan editing parser.
        User request: "{user_text}"

        Output a JSON array of modifications.
        
        Rules:
        - action ∈ ["add", "remove", "modify_time", "change_budget"]
        - For "add": include "destination_data"
        - For "remove": include "destination_id"
        - For "modify_time": include "destination_id" and "fields" (start_time/end_time/day)
        - For "change_budget": include "fields": {"budget": number}

        Only output valid JSON.
        """

        response = await self.text_generator.generate_json(prompt)
        return response