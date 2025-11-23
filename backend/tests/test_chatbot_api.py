import sys
from pathlib import Path
import asyncio
import os

# Load .env từ backend
from dotenv import load_dotenv
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import asyncio
import os

async def test_real_llm_api():
    """Test real LLM API integration (requires API key)"""
    print("\n" + "="*60)
    print("🧪 TESTING REAL LLM API INTEGRATION")
    print("="*60 + "\n")
    
    # Check if API key exists
    api_key = os.getenv("OPEN_ROUTER_API_KEY")
    if not api_key:
        print("⚠️  OPEN_ROUTER_API_KEY not found in environment")
        print("   Set it with: set OPEN_ROUTER_API_KEY=your_key_here")
        print("   Skipping real API tests\n")
        return
    
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}\n")
    
    # Test 1: Simple conversation
    print("📋 Test 1: Simple Conversation")
    try:
        from services.chatbot.llm_service import LLMService
        
        llm = LLMService()
        
        messages = [
            {"role": "system", "content": "Bạn là trợ lý du lịch thông minh của EcomoveX."},
            {"role": "user", "content": "Xin chào! Tôi muốn đi du lịch Đà Nẵng."}
        ]
        
        print("  Sending request to LLM...")
        reply = await llm.generate_reply(messages)
        
        print(f"  ✅ Response received")
        print(f"     User: Xin chào! Tôi muốn đi du lịch Đà Nẵng.")
        print(f"     Bot: {reply}\n")
        
    except Exception as e:
        print(f"  ❌ Simple conversation test failed: {e}\n")
        import traceback
        traceback.print_exc()
    
    # Test 2: Multi-turn conversation
    print("📋 Test 2: Multi-turn Conversation")
    try:
        from services.chatbot.llm_service import LLMService
        
        llm = LLMService()
        
        conversation = [
            {"role": "system", "content": "Bạn là trợ lý du lịch EcomoveX, chuyên về du lịch sinh thái."},
            {"role": "user", "content": "Tôi có ngân sách 5 triệu cho 3 ngày ở Đà Nẵng"},
        ]
        
        print("  Turn 1:")
        reply1 = await llm.generate_reply(conversation)
        print(f"    User: Tôi có ngân sách 5 triệu cho 3 ngày ở Đà Nẵng")
        print(f"    Bot: {reply1[:100]}...")
        
        conversation.append({"role": "assistant", "content": reply1})
        conversation.append({"role": "user", "content": "Gợi ý cho tôi địa điểm thân thiện với môi trường"})
        
        print("  Turn 2:")
        reply2 = await llm.generate_reply(conversation)
        print(f"    User: Gợi ý cho tôi địa điểm thân thiện với môi trường")
        print(f"    Bot: {reply2[:100]}...\n")
        
    except Exception as e:
        print(f"  ❌ Multi-turn test failed: {e}\n")
        import traceback
        traceback.print_exc()
    
    # Test 3: Planning assistance
    print("📋 Test 3: Planning Assistance")
    try:
        from services.chatbot.llm_service import LLMService
        
        llm = LLMService()
        
        messages = [
            {"role": "system", "content": "Bạn là trợ lý lập kế hoạch du lịch. Giúp người dùng tổ chức lịch trình chi tiết."},
            {"role": "user", "content": "Lập kế hoạch chi tiết cho 1 ngày ở Hội An, bắt đầu từ 8h sáng"}
        ]
        
        print("  Requesting detailed itinerary...")
        reply = await llm.generate_reply(messages)
        
        print(f"  ✅ Itinerary received")
        print(f"     Request: Lập kế hoạch chi tiết cho 1 ngày ở Hội An")
        print(f"     Response:\n{reply}\n")
        
    except Exception as e:
        print(f"  ❌ Planning assistance test failed: {e}\n")
        import traceback
        traceback.print_exc()
    
    print("="*60)
    print("✅ REAL API TESTS COMPLETED")
    print("="*60 + "\n")

if __name__ == "__main__":
    # Check for API key first
    if os.getenv("OPEN_ROUTER_API_KEY"):
        asyncio.run(test_real_llm_api())
    else:
        print("File path:", __file__)
        print("ENV path:", env_path)
        print("ENV exists?", env_path.exists())

        print("[DEBUG] API KEY =", os.getenv("OPEN_ROUTER_API_KEY"))
        print("\n⚠️  Set OPEN_ROUTER_API_KEY environment variable to run real API tests")
        print("   Example: set OPEN_ROUTER_API_KEY=your_key_here\n")