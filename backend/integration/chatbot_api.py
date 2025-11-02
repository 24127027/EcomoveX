"""
AI Chatbot API Integration
Provides access to LLM services for conversational AI:
- OpenAI (GPT-4, GPT-3.5)
- Google Gemini
- Anthropic Claude (optional)
"""

import httpx
from typing import Optional, List, Dict, Any, AsyncGenerator
from utils.config import settings
import json


class OpenAIClient:
    """
    Client for OpenAI API (GPT-4, GPT-3.5-turbo, etc.)
    
    Supports:
    - Chat completions
    - Streaming responses
    - Function calling
    - Embeddings
    """
    
    BASE_URL = "https://api.openai.com/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key from settings or parameter."""
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate a chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
                Example: [
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": "Hello!"}
                ]
            model: Model to use (gpt-4, gpt-3.5-turbo, etc.)
            temperature: Creativity level (0.0 to 2.0)
            max_tokens: Maximum tokens in response
            stream: Whether to stream the response
        
        Returns:
            Response dictionary with 'choices' containing the generated text
        """
        url = f"{self.BASE_URL}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming chat completion.
        
        Args:
            messages: List of message dicts
            model: Model to use
            temperature: Creativity level
            max_tokens: Maximum tokens in response
        
        Yields:
            Chunks of the generated text as they arrive
        """
        url = f"{self.BASE_URL}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        async with self.client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        content = chunk["choices"][0]["delta"].get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
    
    async def create_embedding(
        self,
        text: str,
        model: str = "text-embedding-ada-002",
    ) -> List[float]:
        """
        Create an embedding vector for text.
        
        Args:
            text: Text to embed
            model: Embedding model to use
        
        Returns:
            List of floats representing the embedding
        """
        url = f"{self.BASE_URL}/embeddings"
        
        payload = {
            "model": model,
            "input": text,
        }
        
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]


class GeminiClient:
    """
    Client for Google Gemini API.
    
    Supports:
    - Text generation
    - Multi-turn conversations
    - Streaming responses
    """
    
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key from settings or parameter."""
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def generate_content(
        self,
        prompt: str,
        model: str = "gemini-pro",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate text content.
        
        Args:
            prompt: Input prompt
            model: Model to use (gemini-pro, gemini-pro-vision)
            temperature: Creativity level (0.0 to 1.0)
            max_tokens: Maximum tokens in response
        
        Returns:
            Response dictionary with generated content
        """
        url = f"{self.BASE_URL}/models/{model}:generateContent"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
            }
        }
        
        if max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens
        
        params = {"key": self.api_key}
        
        response = await self.client.post(url, json=payload, params=params)
        response.raise_for_status()
        return response.json()
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "gemini-pro",
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Multi-turn conversation.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use
            temperature: Creativity level
        
        Returns:
            Response with generated reply
        """
        url = f"{self.BASE_URL}/models/{model}:generateContent"
        
        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
            }
        }
        
        params = {"key": self.api_key}
        
        response = await self.client.post(url, json=payload, params=params)
        response.raise_for_status()
        return response.json()


class ChatbotHelper:
    """
    Helper class for common chatbot operations using either OpenAI or Gemini.
    """
    
    def __init__(self, provider: str = "openai"):
        """
        Initialize with specified provider.
        
        Args:
            provider: "openai" or "gemini"
        """
        self.provider = provider.lower()
        if self.provider == "openai":
            self.client = OpenAIClient()
        elif self.provider == "gemini":
            self.client = GeminiClient()
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def get_eco_travel_response(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Get a response focused on eco-friendly travel advice.
        
        Args:
            user_message: User's question or message
            conversation_history: Previous messages in the conversation
        
        Returns:
            Bot's response as a string
        """
        system_prompt = """You are an eco-friendly travel assistant for EcomoveX.
Your goal is to help users plan sustainable and environmentally conscious trips.

Key responsibilities:
- Recommend eco-friendly destinations and activities
- Suggest sustainable transportation options (trains, bikes, electric vehicles)
- Provide tips for reducing carbon footprint while traveling
- Recommend eco-conscious hotels and restaurants
- Share information about carbon offsetting
- Encourage responsible tourism practices

Always be helpful, informative, and encouraging about sustainable travel."""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": user_message})
        
        if self.provider == "openai":
            response = await self.client.chat_completion(messages)
            return response["choices"][0]["message"]["content"]
        else:  # gemini
            # Convert to single prompt for Gemini
            full_prompt = f"{system_prompt}\n\nUser: {user_message}"
            response = await self.client.generate_content(full_prompt)
            return response["candidates"][0]["content"]["parts"][0]["text"]
    
    async def close(self):
        """Close the underlying client."""
        await self.client.close()


# Singleton instances
_openai_client_instance: Optional[OpenAIClient] = None
_gemini_client_instance: Optional[GeminiClient] = None
_chatbot_helper_instance: Optional[ChatbotHelper] = None


async def get_openai_client() -> OpenAIClient:
    """Get or create a singleton OpenAI client."""
    global _openai_client_instance
    if _openai_client_instance is None:
        _openai_client_instance = OpenAIClient()
    return _openai_client_instance


async def get_gemini_client() -> GeminiClient:
    """Get or create a singleton Gemini client."""
    global _gemini_client_instance
    if _gemini_client_instance is None:
        _gemini_client_instance = GeminiClient()
    return _gemini_client_instance


async def get_chatbot_helper(provider: str = "openai") -> ChatbotHelper:
    """Get or create a singleton ChatbotHelper."""
    global _chatbot_helper_instance
    if _chatbot_helper_instance is None or _chatbot_helper_instance.provider != provider:
        _chatbot_helper_instance = ChatbotHelper(provider)
    return _chatbot_helper_instance
