from integration.chatbot_groq import GroqAPI

class ChatbotService:
    def __init__(self):
        self.llm = GroqAPI()

    async def handle_user_message(self, data):
        return await self.llm.generate_reply(data.message)
