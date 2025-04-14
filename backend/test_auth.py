import requests
import json
import sys

BASE_URL = "http://localhost:5001/api/auth"

def test_signup():
    payload = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/signup", json=payload)
    print(f"Signup Status Code: {response.status_code}")
    print(f"Signup Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 201

def test_login():
    payload = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/login", json=payload)
    print(f"Login Status Code: {response.status_code}")
    print(f"Login Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        token = response.json().get("token")
        return token
    return None

def test_get_user(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/user", headers=headers)
    print(f"Get User Status Code: {response.status_code}")
    print(f"Get User Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

if __name__ == "__main__":
    print("Testing signup...")
    try:
        signup_success = test_signup()
    except Exception as e:
        print(f"Signup error: {e}")
        signup_success = False
    
    print("\nTesting login...")
    try:
        token = test_login()
        login_success = token is not None
    except Exception as e:
        print(f"Login error: {e}")
        login_success = False
        token = None
    
    if token:
        print("\nTesting get user...")
        try:
            user_success = test_get_user(token)
        except Exception as e:
            print(f"Get user error: {e}")
            user_success = False
    else:
        user_success = False
    
    if signup_success and login_success and user_success:
        print("\n✅ Authentication tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some authentication tests failed")
        sys.exit(1)