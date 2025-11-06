from openai import OpenAI
from typing import List, Dict, Optional, Any
import httpx
from utils.config import settings

class TextGenerator:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key=settings.HUGGINGFACE_API_KEY,
        )
        self.http_client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"},
            timeout=30.0
        )
        self.text_model = "deepseek-ai/DeepSeek-R1-0528"
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 1,
    ) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.text_model,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in chat completion: {e}")
            return "I'm sorry, I encountered an error. Please try again."

    async def generate_text(self, prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        return self.chat_completion(messages)

    async def close(self):
        await self.http_client.aclose()

_text_generator_instance: Optional[TextGenerator] = None

def get_text_generator() -> TextGenerator:
    global _text_generator_instance
    if _text_generator_instance is None:
        _text_generator_instance = TextGenerator()
    return _text_generator_instance