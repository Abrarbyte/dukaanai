import urllib.request
import urllib.parse
import json
import uuid

BASE_URL = "http://127.0.0.1:5000"

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
            return status, json.loads(body)
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode('utf-8'))
        except:
            return e.code, e.read().decode('utf-8')
    except Exception as e:
        return 0, str(e)

# 1. Signup (Using a valid password and unique email)
print("--- TEST 1: SIGNUP ---")
email = f"test_{uuid.uuid4().hex[:6]}@test.com" 
password = "Password123!" 
status1, resp1 = make_request(f"{BASE_URL}/api/auth/signup", data={
    "name": "Test User",
    "email": email,
    "password": password,
    "phone": "9999999999"
})
print("SIGNUP:", status1, resp1)

# 2. Login
print("\n--- TEST 2: LOGIN ---")
status2, resp2 = make_request(f"{BASE_URL}/api/auth/login", data={
    "email": email,
    "password": password
})
print("LOGIN:", status2, resp2)

if status2 != 200:
    print("Login failed. Stopping.")
    exit()

# Get token
token = resp2['data']['access_token']
print("\nTOKEN:", token[:20] + "...")

# 3. Get Stores
print("\n--- TEST 3: GET STORES ---")
headers = {"Authorization": f"Bearer {token}"}
status3, resp3 = make_request(f"{BASE_URL}/api/stores", headers=headers, method='GET')
print("STORES:", status3, resp3)

# 4. Create Store (with case-insensitive test)
print("\n--- TEST 4: CREATE STORE (General) ---")
status4, resp4 = make_request(f"{BASE_URL}/api/stores", headers=headers, data={
    "store_name": "Test Shop Success",
    "store_type": "General",
    "address": "Test Address"
})
print("CREATE STORE:", status4, resp4)
