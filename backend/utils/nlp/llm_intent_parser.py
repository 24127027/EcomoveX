class LLMIntentParser:

    async def parse(self, user_text: str) -> str:
        prompt = f"""
        You classify the user's intent.

        User message: "{user_text}"

        Possible intents:
        - "plan_edit": user wants to change/edit an existing travel plan
        - "plan_query": user wants to ask about the travel plan, generate plan, view plan, optimize plan
        - "chit_chat": casual conversation, greetings, jokes

        Return exactly one intent as plain text (no JSON).
        """

        intent = await self.text_generator.generate_text(prompt)
        intent = intent.strip().lower()

        if intent not in ["plan_edit", "plan_query", "chit_chat"]:
            return "chit_chat"

        return intent
