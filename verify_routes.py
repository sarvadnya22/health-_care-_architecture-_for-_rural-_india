import requests
import time

BASE_URL = "http://127.0.0.1:5000"

def check_route(path, description):
    try:
        response = requests.get(f"{BASE_URL}{path}", timeout=5)
        print(f"[{response.status_code}] {description} ({path})")
        if response.status_code == 500:
            print(f"!!! SERVER ERROR on {path} !!!")
            return False
        return True
    except Exception as e:
        print(f"!!! FAILED to connect to {path}: {e}")
        return False

print("Waiting for server to start...")
time.sleep(5) # Wait for Flask to boot

routes = [
    ("/", "Home Page"),
    ("/pharmacy/login", "Pharmacy Login"),
    ("/health_dept/login", "Health Dept Login"),
    ("/login", "Patient Login")
]

all_passed = True
for path, desc in routes:
    if not check_route(path, desc):
        all_passed = False

if all_passed:
    print("SUCCESS: All checked routes are reachable.")
else:
    print("FAILURE: Some routes failed.")
