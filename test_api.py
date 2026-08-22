import requests
import time

BASE = "http://127.0.0.1:8000"
TS = str(int(time.time()))


def test(name, method, path, data=None, token=None, expect=None):
    url = f"{BASE}{path}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if method == "post" and path == "/api/auth/login":
        resp = requests.post(url, data=data, headers=headers)
    elif data:
        headers["Content-Type"] = "application/json"
        resp = getattr(requests, method)(url, json=data, headers=headers)
    else:
        resp = getattr(requests, method)(url, headers=headers)
    if expect is not None:
        status = "PASS" if resp.status_code == expect else "FAIL"
    else:
        status = "PASS" if resp.status_code < 400 else "FAIL"
    print(f"[{status}] {name} => {resp.status_code}")
    try:
        return resp.status_code, resp.json()
    except:
        return resp.status_code, resp.text


print("=" * 60)
print("NeighborGlow API Test Suite")
print(f"Timestamp: {TS}")
print("=" * 60)

# 1. Health
print("\n--- 1. Health ---")
test("Health check", "get", "/api/health")

# 2. Register
print("\n--- 2. Register ---")
test("Register resident", "post", "/api/auth/register", {
    "username": f"alice_{TS}", "password": "pass123", "role": "resident",
    "real_name": "Alice", "phone": "13800000001"
})
test("Register staff", "post", "/api/auth/register", {
    "username": f"admin_{TS}", "password": "pass123", "role": "staff",
    "real_name": "Admin", "phone": "13900000001"
})

# 3. Login
print("\n--- 3. Login ---")
_, alice_login = test("Login resident", "post", "/api/auth/login",
    data={"username": f"alice_{TS}", "password": "pass123"})
alice_token = alice_login.get("access_token") if isinstance(alice_login, dict) else None

_, admin_login = test("Login staff", "post", "/api/auth/login",
    data={"username": f"admin_{TS}", "password": "pass123"})
admin_token = admin_login.get("access_token") if isinstance(admin_login, dict) else None

# 4. Cases
print("\n--- 4. Cases ---")
_, case1 = test("Create case", "post", "/api/cases", {
    "title": "深夜噪音", "description": "每天晚上11点后楼上邻居拖椅子、走路声音很大，影响休息",
    "category": "noise"
}, token=alice_token)

test("List cases", "get", "/api/cases", token=alice_token)

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
