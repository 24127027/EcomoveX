"""
Test script for EcomoveX API routers
Tests: Authentication, User, Review, and Reward routers
"""
import requests
import json
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def check_server():
    """Check if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def wait_for_server(max_attempts=5):
    """Wait for server to be ready"""
    print("Checking if server is running...")
    for i in range(max_attempts):
        if check_server():
            print(f"{Colors.GREEN}✓ Server is ready!{Colors.END}\n")
            return True
        print(f"Attempt {i+1}/{max_attempts}: Server not ready, waiting...")
        time.sleep(2)
    return False

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}Testing: {name}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_response(response):
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

test_user = {
    "username": "testuser123",
    "email": "test@example.com",
    "password": "testpassword123"
}

access_token = None
user_id = None

def test_authentication():
    global access_token, user_id
    
    print_test("1. AUTHENTICATION ROUTER")
    
    print(f"\n{Colors.YELLOW}1.1 POST /auth/register{Colors.END}")
    response = requests.post(f"{BASE_URL}/auth/register", json=test_user)
    if response.status_code == 201 or response.status_code == 200:
        data = response.json()
        access_token = data.get("access_token")
        user_id = data.get("user_id")
        print_success(f"User registered! User ID: {user_id}")
        print_response(response)
    else:
        print_error(f"Failed to register: {response.status_code}")
        print(response.text)
    
    print(f"\n{Colors.YELLOW}1.2 POST /auth/login{Colors.END}")
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        data = response.json()
        access_token = data.get("access_token")
        user_id = data.get("user_id")
        print_success(f"Login successful! Token: {access_token[:20]}...")
        print_response(response)
    else:
        print_error(f"Failed to login: {response.status_code}")
        print(response.text)

def test_user_router():
    global access_token, user_id
    
    print_test("2. USER ROUTER")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print(f"\n{Colors.YELLOW}2.1 GET /users/me{Colors.END}")
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    if response.status_code == 200:
        print_success("Profile retrieved successfully!")
        print_response(response)
    else:
        print_error(f"Failed to get profile: {response.status_code}")
        print(response.text)
    
    print(f"\n{Colors.YELLOW}2.2 GET /users/{user_id}{Colors.END}")
    response = requests.get(f"{BASE_URL}/users/{user_id}")
    if response.status_code == 200:
        print_success("User retrieved by ID successfully!")
        print_response(response)
    else:
        print_error(f"Failed to get user: {response.status_code}")
        print(response.text)
    
    print(f"\n{Colors.YELLOW}2.3 PUT /users/me/profile{Colors.END}")
    update_data = {
        "eco_point": 100,
        "rank": "Bronze"
    }
    response = requests.put(f"{BASE_URL}/users/me/profile", json=update_data, headers=headers)
    if response.status_code == 200:
        print_success("Profile updated successfully!")
        print_response(response)
    else:
        print_error(f"Failed to update profile: {response.status_code}")
        print(response.text)

def test_review_router():
    global access_token, user_id
    
    print_test("3. REVIEW ROUTER")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print(f"\n{Colors.YELLOW}3.1 POST /reviews/{Colors.END}")
    print("Note: This requires destination ID 1 to exist in the database")
    review_data = {
        "destination_id": 1,
        "content": "Great eco-friendly destination!",
        "status": "published"
    }
    response = requests.post(f"{BASE_URL}/reviews/", json=review_data, headers=headers)
    review_id = None
    if response.status_code == 201:
        data = response.json()
        review_id = data.get("id")
        print_success(f"Review created! Review ID: {review_id}")
        print_response(response)
    else:
        print_error(f"Failed to create review: {response.status_code}")
        print(response.text)
        return
    
    print(f"\n{Colors.YELLOW}3.2 GET /reviews/me{Colors.END}")
    response = requests.get(f"{BASE_URL}/reviews/me", headers=headers)
    if response.status_code == 200:
        print_success("Reviews retrieved successfully!")
        print_response(response)
    else:
        print_error(f"Failed to get reviews: {response.status_code}")
        print(response.text)
    
    if review_id:
        print(f"\n{Colors.YELLOW}3.3 PUT /reviews/{review_id}{Colors.END}")
        update_data = {
            "content": "Updated: Amazing eco-friendly destination!"
        }
        response = requests.put(f"{BASE_URL}/reviews/{review_id}", json=update_data, headers=headers)
        if response.status_code == 200:
            print_success("Review updated successfully!")
            print_response(response)
        else:
            print_error(f"Failed to update review: {response.status_code}")
            print(response.text)
    
    print(f"\n{Colors.YELLOW}3.4 GET /reviews/user/{user_id}{Colors.END}")
    response = requests.get(f"{BASE_URL}/reviews/user/{user_id}")
    if response.status_code == 200:
        print_success("Reviews by user retrieved successfully!")
        print_response(response)
    else:
        print_error(f"Failed to get reviews: {response.status_code}")
        print(response.text)

def test_reward_router():
    global access_token
    
    print_test("4. REWARD ROUTER")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print(f"\n{Colors.YELLOW}4.1 GET /rewards/missions{Colors.END}")
    response = requests.get(f"{BASE_URL}/rewards/missions")
    if response.status_code == 200:
        print_success("Missions retrieved successfully!")
        print_response(response)
    else:
        print_error(f"Failed to get missions: {response.status_code}")
        print(response.text)
    
    print(f"\n{Colors.YELLOW}4.2 POST /rewards/missions (Admin only - expected to fail){Colors.END}")
    mission_data = {
        "name": "First Review",
        "description": "Write your first review",
        "reward_type": "eco_point",
        "action_trigger": "forum_post",
        "value": 10
    }
    response = requests.post(f"{BASE_URL}/rewards/missions", json=mission_data, headers=headers)
    mission_id = None
    if response.status_code == 201:
        data = response.json()
        mission_id = data.get("id")
        print_success(f"Mission created! Mission ID: {mission_id}")
        print_response(response)
    elif response.status_code == 403:
        print_success("Expected 403 Forbidden - user is not admin")
        print(response.json())
    else:
        print_error(f"Unexpected status: {response.status_code}")
        print(response.text)
    
    print(f"\n{Colors.YELLOW}4.3 GET /rewards/me/missions{Colors.END}")
    response = requests.get(f"{BASE_URL}/rewards/me/missions", headers=headers)
    if response.status_code == 200:
        print_success("Completed missions retrieved successfully!")
        print_response(response)
    else:
        print_error(f"Failed to get completed missions: {response.status_code}")
        print(response.text)

def run_all_tests():
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"  ECOMOVEX API ROUTER TESTING")
    print(f"{'='*60}{Colors.END}\n")
    
    if not wait_for_server():
        print_error("Server is not running!")
        print(f"\n{Colors.YELLOW}Please start the server first:{Colors.END}")
        print("  cd backend")
        print("  & ..\.venv\Scripts\\uvicorn.exe main:app --port 8000")
        sys.exit(1)
    
    try:
        test_authentication()
        test_user_router()
        test_review_router()
        test_reward_router()
        
        print(f"\n{Colors.GREEN}{'='*60}")
        print(f"  ALL TESTS COMPLETED!")
        print(f"{'='*60}{Colors.END}\n")
        
    except requests.exceptions.ConnectionError:
        print_error("Lost connection to server!")
        print("Make sure the server is still running.")
    except Exception as e:
        print_error(f"Test suite failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()
