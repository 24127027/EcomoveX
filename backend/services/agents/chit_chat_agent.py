class ChitChatAgent:
    async def chat(self, user_text: str):
        # simple LLM call để trả reply
        return f"Bot chat reply: {user_text}"
