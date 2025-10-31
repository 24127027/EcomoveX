import requests
import json

BASE_URL = "http://127.0.0.1:8000"

# Login
login_data = {
    "email": "carbon@test.com",
    "password": "testpass123"
}
response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
print(f"Login Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    token = data.get("access_token")
    print(f"Token: {token[:50]}...")
    
    # Try to create carbon emission
    headers = {"Authorization": f"Bearer {token}"}
    carbon_data = {
        "vehicle_type": "car",
        "distance_km": 50.0,
        "fuel_type": "petrol"
    }
    
    print("\nTrying to create carbon emission...")
    response = requests.post(f"{BASE_URL}/carbon/calculate", json=carbon_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
else:
    print(f"Login failed: {response.text}")
