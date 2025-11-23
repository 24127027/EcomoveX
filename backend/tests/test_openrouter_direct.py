import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


# Load .env từ backend
from dotenv import load_dotenv
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)



import asyncio
import os
import httpx

async def test_openrouter_direct():
    """Direct test of OpenRouter API"""
    print("\n" + "="*60)
    print("🔍 TESTING OPENROUTER API DIRECTLY")
    print("="*60 + "\n")
    
    api_key = os.getenv("OPEN_ROUTER_API_KEY")
    
    if not api_key:
        print("❌ No API key found!")
        return
    
    print(f"✅ API Key: {api_key[:10]}...{api_key[-4:]}\n")
    
    # Test 1: List available models
    print("📋 Test 1: List Available Models")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            
            print(f"Status: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"✅ Found {len(data.get('data', []))} models")
                
                # Show free models
                free_models = [m for m in data.get('data', []) if 'free' in m.get('id', '').lower()]
                print(f"\nFree models available:")
                for model in free_models[:5]:
                    print(f"  - {model['id']}")
            else:
                print(f"❌ Error: {resp.text}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 2: Try a simple chat completion
    print("\n📋 Test 2: Simple Chat Completion")
    
    models_to_try = [
        "meta-llama/llama-3.1-8b-instruct:free",
        "google/gemini-2.0-flash-exp:free",
        "mistralai/mistral-7b-instruct:free"
    ]
    
    for model in models_to_try:
        print(f"\nTrying model: {model}")
        
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "EcomoveX",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": [
                    {"role": "user", "content": "Hello! Say hi back in one sentence."}
                ],
                "temperature": 0.7,
                "max_tokens": 50
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    json=payload,
                    headers=headers
                )
                
                print(f"  Status: {resp.status_code}")
                
                if resp.status_code == 200:
                    data = resp.json()
                    reply = data["choices"][0]["message"]["content"]
                    print(f"  ✅ Success!")
                    print(f"  Reply: {reply}")
                    break  # Found a working model
                else:
                    print(f"  ❌ Error: {resp.text[:200]}")
                    
        except Exception as e:
            print(f"  ❌ Exception: {e}")
    
    print("\n" + "="*60)
    print("✅ DIRECT API TEST COMPLETED")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(test_openrouter_direct())