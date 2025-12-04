from integration.text_generator_api import TextGeneratorAPI
from typing import Optional


class ChitChatAgent:
    """Agent xử lý các tin nhắn chat thông thường."""
    
    def __init__(self):
        self.model = TextGeneratorAPI()
        self.system_prompt = """You are EcomoveX's friendly travel assistant. 
Be helpful, friendly, and concise. Guide users to use 'add', 'remove', 'view plan' for trip planning."""
    
    async def chat(self, user_text: str, context: Optional[list] = None) -> str:
        """Xử lý tin nhắn chat thông thường."""
        try:
            messages = [{"role": "system", "content": self.system_prompt}]
            if context:
                messages.extend(context[-10:])
            messages.append({"role": "user", "content": user_text})
            return await self.model.generate_reply(messages)
        except Exception as e:
            return f"Xin lỗi, tôi gặp sự cố. Bạn có thể thử lại không?"
