import requests
import sys

BASE_URL = "http://127.0.0.1:5000"

def test_login(role_name, login_url, dashboard_url, payload, success_indicator=None):
    print(f"--- Testing {role_name} Login ---")
    session = requests.Session()
    
    # 1. GET Login Page
    try:
        r = session.get(f"{BASE_URL}{login_url}")
        if r.status_code != 200:
            print(f"FAILED: Could not reach login page {login_url}")
            return False
    except Exception as e:
        print(f"FAILED: Connection refused to {BASE_URL}")
        return False

    # 2. POST Credentials
    try:
        r = session.post(f"{BASE_URL}{login_url}", data=payload)
        
        # Check if redirected to dashboard
        if r.url == f"{BASE_URL}{dashboard_url}":
            print(f"SUCCESS: Redirected to {dashboard_url}")
            return True
        elif success_indicator and success_indicator in r.text:
             print(f"SUCCESS: Found '{success_indicator}' in response")
             return True
        else:
            print(f"FAILED: Expected {dashboard_url}, got {r.url}")
            # print(f"Response content: {r.text[:500]}...") 
            return False
            
    except Exception as e:
        print(f"FAILED: Error during POST: {e}")
        return False

# Test ASHA
asha_payload = {
    "phone_number": "+919307202913",
    "password": "asha123"
}
asha_result = test_login("ASHA Worker", "/worker_login", "/dashboard", asha_payload)

# Test Doctor
doc_payload = {
    "email": "doc@health.com",
    "password": "doc123"
}
doc_result = test_login("Doctor", "/doctor/login", "/doctor/dashboard", doc_payload)

if asha_result and doc_result:
    print("\nALL LOGIN TESTS PASSED")
    sys.exit(0)
else:
    print("\nSOME TESTS FAILED")
    sys.exit(1)
