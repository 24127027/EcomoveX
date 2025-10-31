import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

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
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

access_token = None
user_id = None
emission_id = None

def test_authentication():
    global access_token, user_id
    
    print_test("AUTHENTICATION")
    
    print(f"\n{Colors.YELLOW}1. Register/Login User{Colors.END}")
    
    register_data = {
        "username": "carbontest",
        "email": "carbon@test.com",
        "password": "testpass123"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    
    if response.status_code in [200, 201, 400]:
        if response.status_code == 400:
            print("User already exists, attempting login...")
            login_data = {
                "email": register_data["email"],
                "password": register_data["password"]
            }
            response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            user_id = data.get("user_id")
            print_success(f"Authenticated! User ID: {user_id}")
            print_response(response)
        else:
            print_error(f"Authentication failed: {response.status_code}")
            print(response.text)
            return False
    else:
        print_error(f"Authentication failed: {response.status_code}")
        print(response.text)
        return False
    
    return True

def test_carbon_calculate():
    global emission_id
    
    print_test("CARBON CALCULATION")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print(f"\n{Colors.YELLOW}2.1 POST /carbon/calculate - Car with Petrol{Colors.END}")
    carbon_data = {
        "vehicle_type": "car",
        "distance_km": 50.0,
        "fuel_type": "petrol"
    }
    response = requests.post(f"{BASE_URL}/carbon/calculate", json=carbon_data, headers=headers)
    if response.status_code == 201:
        data = response.json()
        emission_id = data.get("id")
        print_success(f"Carbon calculated! Emission ID: {emission_id}")
        print_response(response)
        print(f"Expected: ~8.55 kg CO2 (0.171 * 50)")
    else:
        print_error(f"Failed to calculate: {response.status_code}")
        print_response(response)
    
    print(f"\n{Colors.YELLOW}2.2 POST /carbon/calculate - Bus with Electric{Colors.END}")
    carbon_data = {
        "vehicle_type": "bus",
        "distance_km": 100.0,
        "fuel_type": "electric"
    }
    response = requests.post(f"{BASE_URL}/carbon/calculate", json=carbon_data, headers=headers)
    if response.status_code == 201:
        print_success("Carbon calculated!")
        print_response(response)
        print(f"Expected: ~2.7 kg CO2 (0.027 * 100)")
    else:
        print_error(f"Failed to calculate: {response.status_code}")
        print_response(response)
    
    print(f"\n{Colors.YELLOW}2.3 POST /carbon/calculate - Walk/Cycle{Colors.END}")
    carbon_data = {
        "vehicle_type": "walk or cycle",
        "distance_km": 10.0,
        "fuel_type": "none"
    }
    response = requests.post(f"{BASE_URL}/carbon/calculate", json=carbon_data, headers=headers)
    if response.status_code == 201:
        print_success("Carbon calculated!")
        print_response(response)
        print(f"Expected: 0.0 kg CO2")
    else:
        print_error(f"Failed to calculate: {response.status_code}")
        print_response(response)
    
    print(f"\n{Colors.YELLOW}2.4 POST /carbon/calculate - Motorbike with Petrol{Colors.END}")
    carbon_data = {
        "vehicle_type": "motorbike",
        "distance_km": 25.0,
        "fuel_type": "petrol"
    }
    response = requests.post(f"{BASE_URL}/carbon/calculate", json=carbon_data, headers=headers)
    if response.status_code == 201:
        print_success("Carbon calculated!")
        print_response(response)
        print(f"Expected: ~2.575 kg CO2 (0.103 * 25)")
    else:
        print_error(f"Failed to calculate: {response.status_code}")
        print_response(response)

def test_carbon_retrieval():
    print_test("CARBON RETRIEVAL")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print(f"\n{Colors.YELLOW}3.1 GET /carbon/me - Get All My Emissions{Colors.END}")
    response = requests.get(f"{BASE_URL}/carbon/me", headers=headers)
    if response.status_code == 200:
        print_success("Emissions retrieved!")
        print_response(response)
    else:
        print_error(f"Failed to retrieve: {response.status_code}")
        print_response(response)
    
    print(f"\n{Colors.YELLOW}3.2 GET /carbon/me/total - Get Total Carbon Footprint{Colors.END}")
    response = requests.get(f"{BASE_URL}/carbon/me/total", headers=headers)
    if response.status_code == 200:
        print_success("Total calculated!")
        print_response(response)
    else:
        print_error(f"Failed to get total: {response.status_code}")
        print_response(response)
    
    if emission_id:
        print(f"\n{Colors.YELLOW}3.3 GET /carbon/{emission_id} - Get Specific Emission{Colors.END}")
        response = requests.get(f"{BASE_URL}/carbon/{emission_id}", headers=headers)
        if response.status_code == 200:
            print_success("Specific emission retrieved!")
            print_response(response)
        else:
            print_error(f"Failed to retrieve: {response.status_code}")
            print_response(response)

def test_carbon_time_queries():
    print_test("CARBON TIME-BASED QUERIES")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    current_date = datetime.now().isoformat()
    current_year = datetime.now().year
    
    print(f"\n{Colors.YELLOW}4.1 GET /carbon/me/total/day - Today's Emissions{Colors.END}")
    response = requests.get(f"{BASE_URL}/carbon/me/total/day?date={current_date}", headers=headers)
    if response.status_code == 200:
        print_success("Daily total retrieved!")
        print_response(response)
    else:
        print_error(f"Failed: {response.status_code}")
        print_response(response)
    
    print(f"\n{Colors.YELLOW}4.2 GET /carbon/me/total/week - This Week's Emissions{Colors.END}")
    response = requests.get(f"{BASE_URL}/carbon/me/total/week?date={current_date}", headers=headers)
    if response.status_code == 200:
        print_success("Weekly total retrieved!")
        print_response(response)
    else:
        print_error(f"Failed: {response.status_code}")
        print_response(response)
    
    print(f"\n{Colors.YELLOW}4.3 GET /carbon/me/total/month - This Month's Emissions{Colors.END}")
    response = requests.get(f"{BASE_URL}/carbon/me/total/month?date={current_date}", headers=headers)
    if response.status_code == 200:
        print_success("Monthly total retrieved!")
        print_response(response)
    else:
        print_error(f"Failed: {response.status_code}")
        print_response(response)
    
    print(f"\n{Colors.YELLOW}4.4 GET /carbon/me/total/year - This Year's Emissions{Colors.END}")
    response = requests.get(f"{BASE_URL}/carbon/me/total/year?year={current_year}", headers=headers)
    if response.status_code == 200:
        print_success("Yearly total retrieved!")
        print_response(response)
    else:
        print_error(f"Failed: {response.status_code}")
        print_response(response)

def test_carbon_update_delete():
    print_test("CARBON UPDATE & DELETE")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    if emission_id:
        print(f"\n{Colors.YELLOW}5.1 PUT /carbon/{emission_id} - Update Emission{Colors.END}")
        update_data = {
            "distance_km": 75.0
        }
        response = requests.put(f"{BASE_URL}/carbon/{emission_id}", json=update_data, headers=headers)
        if response.status_code == 200:
            print_success("Emission updated!")
            print_response(response)
        else:
            print_error(f"Failed to update: {response.status_code}")
            print_response(response)
        
        print(f"\n{Colors.YELLOW}5.2 DELETE /carbon/{emission_id} - Delete Emission{Colors.END}")
        response = requests.delete(f"{BASE_URL}/carbon/{emission_id}", headers=headers)
        if response.status_code == 200:
            print_success("Emission deleted!")
            print_response(response)
        else:
            print_error(f"Failed to delete: {response.status_code}")
            print_response(response)

def run_all_tests():
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"  CARBON ROUTER TESTING")
    print(f"{'='*60}{Colors.END}\n")
    
    if not test_authentication():
        print_error("\nAuthentication failed. Cannot continue tests.")
        return
    
    test_carbon_calculate()
    test_carbon_retrieval()
    test_carbon_time_queries()
    test_carbon_update_delete()
    
    print(f"\n{Colors.GREEN}{'='*60}")
    print(f"  ALL TESTS COMPLETED!")
    print(f"{'='*60}{Colors.END}\n")

if __name__ == "__main__":
    try:
        run_all_tests()
    except Exception as e:
        print_error(f"Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
