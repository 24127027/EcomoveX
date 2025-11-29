import httpx
from openai import OpenAI

from utils.config import settings


class TextGeneratorAPI:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1/chat/completions",
            api_key=settings.HUGGINGFACE_API_KEY,
        )
        self.http_client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {settings.OPEN_ROUTER_API_KEY}",
                "Content-Type": "application/json",
                "X-Title": "EcomoveX",
                "Referer": "http://localhost:3000",
                "Origin": "http://localhost:3000",
            },
            timeout=30.0,
        )
        self.text_model = settings.OPEN_ROUTER_MODEL_NAME or "meta-llama/llama-3.3-70b-instruct"

    async def close(self):
        await self.http_client.aclose()

    async def generate_reply(
        self,
        context_messages: list,
        api_key: str = settings.OPEN_ROUTER_API_KEY,
        model: str = settings.OPEN_ROUTER_MODEL_NAME,
    ) -> str:
        if model is None:
            model = self.text_model

        payload = {
            "model": model,
            "messages": context_messages,
            "temperature": 0.7,
            "max_tokens": 1000,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    self.client.base_url, json=payload, headers=self.http_client.headers
                )
                resp.raise_for_status()

                if not resp.text or resp.text.strip() == "":
                    raise Exception("Empty response from LLM")

                try:
                    data = resp.json()
                except Exception as json_err:
                    raise Exception("LLM returned non-JSON body") from json_err

                if "choices" not in data or len(data["choices"]) == 0:
                    raise Exception("Invalid response format: missing 'choices'")

                reply = data["choices"][0]["message"]["content"]
                return reply

        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP Error: {e.response.text}")
        except Exception as e:
            raise Exception(f"LLM Error: {str(e)}")


async def create_text_generator_api() -> TextGeneratorAPI:
    return TextGeneratorAPI()
