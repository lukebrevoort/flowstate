import requests
import json
import sys

# First, get a token
def get_token():
    payload = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post("http://localhost:5001/api/auth/login", json=payload)
    if response.status_code == 200:
        return response.json().get("token")
    return None

def test_chat():
    token = get_token()
    if not token:
        print("❌ Failed to get authentication token")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"message": "Find some time tonight and tomorrow that so I can finish my CS135 Assignments"}
    
    print("Sending chat request...")
    response = requests.post("http://localhost:5001/api/chat", headers=headers, json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2) if response.status_code == 200 else response.text}")
    
    return response.status_code == 200

if __name__ == "__main__":
    success = test_chat()
    print("✅ Chat test passed!" if success else "❌ Chat test failed")
    sys.exit(0 if success else 1)