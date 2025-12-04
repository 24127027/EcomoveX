#!/usr/bin/env python3
"""
Script để test API friend request by username
Test trực tiếp với backend đang chạy
"""

import requests
import json

# CONFIGURATION
BASE_URL = "http://localhost:8000"

# Test data từ database
TEST_USERS = {
    "user1": {"username": "tri", "email": "hodinht2@gmail.com", "password": "your_password"},
    "user2": {"username": "dinhtri", "email": "hodinhtri3010@gmail.com", "password": "your_password"}
}


def login(username: str, password: str):
    """Login và lấy token"""
    print(f"\n🔐 Logging in as '{username}'...")
    
    url = f"{BASE_URL}/auth/login"
    data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            print(f"   ✅ Login successful")
            print(f"   Token: {token[:50]}...")
            return token
        else:
            print(f"   ❌ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def send_friend_request_by_username(token: str, target_username: str):
    """Gửi friend request bằng username"""
    print(f"\n📤 Sending friend request to '{target_username}'...")
    
    url = f"{BASE_URL}/friends/request/by-username"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "username": target_username
    }
    
    print(f"   URL: {url}")
    print(f"   Headers: {headers}")
    print(f"   Body: {json.dumps(data)}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"\n   Response Status: {response.status_code}")
        print(f"   Response Body: {response.text}")
        
        if response.status_code == 201:
            print(f"   ✅ Friend request sent successfully!")
            return response.json()
        elif response.status_code == 404:
            print(f"   ❌ 404 Not Found - User '{target_username}' not found")
            print(f"   Detail: {response.json().get('detail', 'No detail')}")
        elif response.status_code == 400:
            print(f"   ⚠️  400 Bad Request - {response.json().get('detail', 'No detail')}")
        else:
            print(f"   ❌ Unexpected error")
        
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def get_friends(token: str):
    """Lấy danh sách friends"""
    print(f"\n📋 Getting friends list...")
    
    url = f"{BASE_URL}/friends/"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            friends = response.json()
            print(f"   ✅ Found {len(friends)} friends")
            for f in friends:
                print(f"      - Friend ID: {f.get('friend_id')}, Status: {f.get('status')}")
            return friends
        else:
            print(f"   ❌ Error: {response.text}")
            return []
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []


def test_api_endpoints():
    """Test toàn bộ flow"""
    print("=" * 80)
    print("🧪 TESTING FRIEND REQUEST BY USERNAME API")
    print("=" * 80)
    
    # Lấy credentials từ user input
    print("\n📝 Enter credentials for testing:")
    print("   (Leave blank to use defaults)")
    
    user1_pass = input(f"Password for '{TEST_USERS['user1']['username']}': ").strip()
    if not user1_pass:
        print("⚠️  Using default password - may not work if you changed it!")
        user1_pass = TEST_USERS['user1']['password']
    
    # Test 1: Login as user1
    token1 = login(TEST_USERS['user1']['username'], user1_pass)
    if not token1:
        print("\n❌ Cannot proceed without login token")
        print("💡 Make sure:")
        print("   1. Backend server is running (uvicorn main:app)")
        print("   2. Credentials are correct")
        return
    
    # Test 2: Send friend request to user2
    target_username = TEST_USERS['user2']['username']
    print(f"\n{'='*80}")
    print(f"TEST: Send friend request from '{TEST_USERS['user1']['username']}' to '{target_username}'")
    print(f"{'='*80}")
    
    result = send_friend_request_by_username(token1, target_username)
    
    # Test 3: Get friends list
    get_friends(token1)
    
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    
    if result:
        print("✅ Friend request API is working correctly!")
    else:
        print("❌ Friend request failed - check logs above")
        print("\n💡 Common issues:")
        print("   1. Server not running: Start with 'uvicorn main:app --reload'")
        print("   2. Wrong credentials: Check your password")
        print("   3. Username typo: Must match exactly (case-insensitive)")
        print("   4. Already friends: Cannot send request again")


def test_direct_curl():
    """Print curl command để test thủ công"""
    print("\n" + "=" * 80)
    print("🔧 MANUAL TESTING WITH CURL")
    print("=" * 80)
    
    print("\nStep 1: Login to get token")
    print(f"""
curl -X POST {BASE_URL}/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{{"username": "tri", "password": "YOUR_PASSWORD"}}'
    """)
    
    print("\nStep 2: Send friend request (replace YOUR_TOKEN)")
    print(f"""
curl -X POST {BASE_URL}/friends/request/by-username \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{{"username": "dinhtri"}}'
    """)


if __name__ == "__main__":
    import sys
    
    if "--curl" in sys.argv:
        test_direct_curl()
    else:
        try:
            test_api_endpoints()
        except KeyboardInterrupt:
            print("\n\n⚠️  Test cancelled by user")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
