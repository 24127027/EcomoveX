import httpx

from utils.config import settings


class TextGeneratorAPI:
    def __init__(self):
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {settings.OPEN_ROUTER_API_KEY}",
            "Content-Type": "application/json",
            "X-Title": "EcomoveX",
            "Referer": "http://localhost:3000",
            "Origin": "http://localhost:3000",
        }
        self.text_model = (
            settings.OPEN_ROUTER_MODEL_NAME or "meta-llama/llama-3.3-70b-instruct"
        )

    async def generate_reply(
        self,
        context_messages: list,
        api_key: str = settings.OPEN_ROUTER_API_KEY,
        model: str = settings.OPEN_ROUTER_MODEL_NAME,
    ) -> str:
        if model is None:
            model = self.text_model

        headers = self.headers.copy()
        if api_key and api_key != settings.OPEN_ROUTER_API_KEY:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "model": model,
            "messages": context_messages,
            "temperature": 0.7,
            "max_tokens": 1000,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    self.base_url, json=payload, headers=headers
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
