import sys
from pathlib import Path

# Fix the path - go up TWO levels to reach backend
backend_dir = Path(__file__).parent.parent  # Change from parent to parent.parent
sys.path.insert(0, str(backend_dir))

import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

async def test_llm_service():
    """Test suite for LLM Service"""
    print("\n" + "="*60)
    print("🧪 TESTING LLM SERVICE")
    print("="*60 + "\n")
    
    # Debug: Print the path
    print(f"Backend directory: {backend_dir}")
    print(f"Python path: {sys.path[:3]}\n")
    
    # Test 1: LLMService initialization
    print("📋 Test 1: LLMService Initialization")
    try:
        from services.chatbot.llm_service import LLMService
        
        # Test with default values
        llm = LLMService()
        assert llm.api_key is not None or llm.api_key == os.getenv("OPEN_ROUTER_API_KEY")
        assert llm.model is not None
        assert llm.url == "https://openrouter.ai/api/v1/chat/completions"
        print(f"  ✅ LLMService initialized")
        print(f"     Model: {llm.model}")
        print(f"     URL: {llm.url}\n")
        
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}\n")
        import traceback
        traceback.print_exc()
        return
    
    # Test 2: Mock LLM generate_reply
    print("📋 Test 2: Mock LLM Generate Reply")
    try:
        from services.chatbot.llm_service import LLMService
        
        llm = LLMService()
        
        # Mock the httpx client
        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock response
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": "Xin chào! Tôi có thể giúp gì cho bạn về chuyến du lịch?"
                        }
                    }
                ]
            }
            mock_response.raise_for_status = MagicMock()
            
            # Setup mock client
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            # Test generate_reply
            context_messages = [
                {"role": "system", "content": "Bạn là trợ lý du lịch"},
                {"role": "user", "content": "Xin chào"}
            ]
            
            reply = await llm.generate_reply(context_messages)
            
            assert reply == "Xin chào! Tôi có thể giúp gì cho bạn về chuyến du lịch?"
            print(f"  ✅ Mock LLM reply generated successfully")
            print(f"     Reply: {reply}\n")
            
    except Exception as e:
        print(f"  ❌ Mock generate_reply failed: {e}\n")
        import traceback
        traceback.print_exc()
    
    # Test 3: ChatbotMessageService initialization
    print("📋 Test 3: ChatbotMessageService Initialization")
    try:
        from services.chatbot.llm_service import ChatbotMessageService
        from utils.config import settings
        
        # Create test database session
        engine = create_async_engine(
            f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}",
            echo=False
        )
        
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            chatbot_service = ChatbotMessageService(session)
            
            assert chatbot_service.db is not None
            assert chatbot_service.repo is not None
            assert chatbot_service.context_mgr is not None
            assert chatbot_service.planner is not None
            assert chatbot_service.llm is not None
            
            print(f"  ✅ ChatbotMessageService initialized successfully\n")
        
        await engine.dispose()
        
    except Exception as e:
        print(f"  ❌ ChatbotMessageService initialization failed: {e}\n")
        import traceback
        traceback.print_exc()
    
    # ... rest of your test code ...
    
    print("="*60)
    print("✅ ALL LLM SERVICE TESTS COMPLETED")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(test_llm_service())