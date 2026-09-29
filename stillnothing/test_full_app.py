import urllib.request
import urllib.parse
import json
import uuid

BASE_URL = "http://127.0.0.1:5000"

def make_req(url, data=None, token=None, method='POST'):
    headers = {}
    if data is not None:
        data_bytes = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    else:
        data_bytes = None

    if token:
        headers['Authorization'] = f"Bearer {token}"

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
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

print("=============================================")
print("RUNNING FULL END-TO-END BACKEND API TESTS")
print("=============================================\n")

# 1. Signup
email = f"user_{uuid.uuid4().hex[:6]}@example.com"
password = "Password123!"
print(f"1. Testing Signup ({email})...")
s1, r1 = make_req(f"{BASE_URL}/api/auth/signup", data={
    "name": "Full Test User",
    "email": email,
    "password": password,
    "phone": "9876543210"
})
assert s1 == 201, f"Signup failed: {s1} {r1}"
token = r1['data']['access_token']
print("   [PASS] Signup Successful!\n")

# 2. Login
print("2. Testing Login...")
s2, r2 = make_req(f"{BASE_URL}/api/auth/login", data={
    "email": email,
    "password": password
})
assert s2 == 200, f"Login failed: {s2} {r2}"
token = r2['data']['access_token']
print("   [PASS] Login Successful!\n")

# 3. Create Store
print("3. Testing Create Store...")
s3, r3 = make_req(f"{BASE_URL}/api/stores", data={
    "store_name": "Apex Electronics",
    "store_type": "Electronics",
    "address": "123 Tech Park, Bangalore"
}, token=token)
assert s3 == 201, f"Create Store failed: {s3} {r3}"
store_id = r3['data']['store']['id']
print(f"   [PASS] Store Created! Store ID: {store_id}\n")

# 4. Add Product
print("4. Testing Add Product...")
s4, r4 = make_req(f"{BASE_URL}/api/stores/{store_id}/products", data={
    "name": "Wireless Headphones",
    "category": "Electronics",
    "purchase_price": 1500.0,
    "selling_price": 2499.0,
    "stock_quantity": 25,
    "min_stock_alert": 5,
    "barcode": "8901234567890"
}, token=token)
assert s4 == 201, f"Add Product failed: {s4} {r4}"
product_id = r4['data']['product']['id']
print(f"   [PASS] Product Added! Product ID: {product_id}\n")

# 5. List Products
print("5. Testing List Products...")
s5, r5 = make_req(f"{BASE_URL}/api/stores/{store_id}/products", token=token, method='GET')
assert s5 == 200, f"List Products failed: {s5} {r5}"
print(f"   [PASS] Fetched {len(r5['data']['products'])} Products!\n")

# 6. Add Customer
print("6. Testing Add Customer...")
s6, r6 = make_req(f"{BASE_URL}/api/stores/{store_id}/customers", data={
    "name": "Rahul Sharma",
    "phone": "9988776655",
    "email": "rahul@example.com"
}, token=token)
assert s6 == 201, f"Add Customer failed: {s6} {r6}"
customer_id = r6['data']['customer']['id']
print(f"   [PASS] Customer Added! Customer ID: {customer_id}\n")

# 7. Record Sale / Create Invoice
print("7. Testing Create Sale...")
s7, r7 = make_req(f"{BASE_URL}/api/stores/{store_id}/sales", data={
    "product_id": product_id,
    "quantity_sold": 2,
    "selling_price": 2499.0,
    "customer_id": customer_id,
    "payment_mode": "upi",
    "discount": 100.0
}, token=token)
assert s7 == 201, f"Create Sale failed: {s7} {r7}"
sale_id = r7['data']['sale']['id']
print(f"   [PASS] Sale Created! Sale ID: {sale_id}, Total: Rs.{r7['data']['sale']['total_amount']}\n")

# 8. Get Sales Reports
print("8. Testing Get Sales Summary Report...")
s8, r8 = make_req(f"{BASE_URL}/api/stores/{store_id}/reports/summary", token=token, method='GET')
assert s8 == 200, f"Get Report failed: {s8} {r8}"
print(f"   [PASS] Sales Summary: Revenue = Rs.{r8['data']['total_revenue']}, Profit = Rs.{r8['data']['total_profit']}\n")

print("=============================================")
print("ALL 8 BACKEND API ENDPOINTS PASSED CLEANLY!")
print("=============================================")
