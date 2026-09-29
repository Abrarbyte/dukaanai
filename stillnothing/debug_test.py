import urllib.request
import urllib.parse
import json
import uuid

BASE_URL = "http://127.0.0.1:5000/api"

def make_request(url, data=None, headers=None, method='POST'):
    if headers is None:
        headers = {}
    if data:
        data = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            body = response.read().decode('utf-8')
            return status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return 0, str(e)

def test_flow():
    # 1. Signup
    email = f"test_{uuid.uuid4().hex[:6]}@example.com"
    print(f"--- Step 1: Signing up with {email} ---")
    signup_data = {
        "name": "Test User",
        "email": email,
        "password": "Password123!",
        "phone": "9876543210"
    }
    
    status, body = make_request(f"{BASE_URL}/auth/signup", data=signup_data)
    print(f"Status: {status}")
    print(f"Response: {body}\n")
    
    if status != 201:
        print("Signup failed. Stopping.")
        return

    # 2. Get Token
    try:
        resp_json = json.loads(body)
        token = resp_json.get('data', {}).get('access_token')
    except:
        token = None

    if not token:
        print("No token in response. Stopping.")
        return

    # 3. Create Store
    print("--- Step 3: Creating Store with token ---")
    store_data = {
        "store_name": "Test Store",
        "store_type": "Retail",
        "address": "123 Test St"
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    status, body = make_request(f"{BASE_URL}/stores", data=store_data, headers=headers)
    print(f"Status: {status}")
    print(f"Response: {body}")

if __name__ == "__main__":
    test_flow()
