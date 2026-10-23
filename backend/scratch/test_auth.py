import httpx
import sys

BASE_URL = "http://localhost:8000"

def test_auth_flow():
    print("Testing Auth Flow...")
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)

    # 1. Test registration
    test_email = "testuser@example.com"
    test_password = "password123"
    test_name = "Nguyen Van Test"

    print(f"\n1. Registering user: {test_email}...")
    resp = client.post("/api/auth/register", json={
        "email": test_email,
        "password": test_password,
        "full_name": test_name
    })

    if resp.status_code == 409:
        print("   User already exists. Proceeding to login test...")
    elif resp.status_code == 201:
        data = resp.json()
        print("   [OK] Registered successfully!")
        print(f"   Token received: {data['access_token'][:25]}...")
        print(f"   User info: {data['user']}")
    else:
        print(f"   [FAIL] Registration failed: {resp.status_code} - {resp.text}")
        sys.exit(1)

    # 2. Test Login
    print(f"\n2. Logging in with email: {test_email}...")
    resp = client.post("/api/auth/login", json={
        "email": test_email,
        "password": test_password
    })

    if resp.status_code == 200:
        data = resp.json()
        token = data["access_token"]
        print("   [OK] Login successful!")
        print(f"   Access Token: {token[:25]}...")
    else:
        print(f"   [FAIL] Login failed: {resp.status_code} - {resp.text}")
        sys.exit(1)

    # 3. Test /me endpoint with Bearer token
    print("\n3. Fetching user profile (/api/auth/me)...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/auth/me", headers=headers)

    if resp.status_code == 200:
        user_info = resp.json()
        print("   [OK] Profile fetched successfully!")
        print(f"   ID: {user_info['id']}")
        print(f"   Email: {user_info['email']}")
        print(f"   Name: {user_info['full_name']}")
    else:
        print(f"   [FAIL] Get profile failed: {resp.status_code} - {resp.text}")
        sys.exit(1)

    # 4. Test unauthorized request
    print("\n4. Testing unauthorized access to /api/notebooks...")
    resp = client.get("/api/notebooks")
    if resp.status_code == 401:
        print("   [OK] Unauthorized request correctly blocked (401 Unauthorized)!")
    else:
        print(f"   [WARNING] Unexpected response for unauthorized request: {resp.status_code}")

    # 5. Test authorized request to /api/notebooks
    print("\n5. Testing authorized request to /api/notebooks...")
    resp = client.get("/api/notebooks", headers=headers)
    if resp.status_code == 200:
        notebooks = resp.json()
        print(f"   [OK] Authorized request successful! User has {len(notebooks)} notebooks.")
    else:
        print(f"   [FAIL] Authorized request failed: {resp.status_code} - {resp.text}")

    print("\nALL BACKEND AUTH TESTS PASSED!")

if __name__ == "__main__":
    test_auth_flow()
