import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db

@pytest.mark.asyncio
async def test_auth_full_api_flow():
    # Initialize DB tables if not already created
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        test_email = "pytest_user@example.com"
        test_password = "password123"
        test_name = "Test User Pytest"

        # 1. Register new user
        reg_resp = await client.post(
            "/api/auth/register",
            json={
                "email": test_email,
                "password": test_password,
                "full_name": test_name
            }
        )
        # If user already exists from prior test runs, 409 is acceptable, else 201
        assert reg_resp.status_code in (201, 409)
        if reg_resp.status_code == 201:
            data = reg_resp.json()
            assert "access_token" in data
            assert data["user"]["email"] == test_email
            assert data["user"]["full_name"] == test_name

        # 2. Re-registering existing user should return 409 Conflict
        re_reg_resp = await client.post(
            "/api/auth/register",
            json={
                "email": test_email,
                "password": test_password,
                "full_name": test_name
            }
        )
        assert re_reg_resp.status_code == 409
        assert "Email này đã được sử dụng" in re_reg_resp.json()["detail"]

        # 3. Login with wrong password should fail (401)
        wrong_login_resp = await client.post(
            "/api/auth/login",
            json={
                "email": test_email,
                "password": "WrongPassword123!"
            }
        )
        assert wrong_login_resp.status_code == 401
        assert "Email hoặc mật khẩu không đúng" in wrong_login_resp.json()["detail"]

        # 4. Login with correct password (200)
        login_resp = await client.post(
            "/api/auth/login",
            json={
                "email": test_email,
                "password": test_password
            }
        )
        assert login_resp.status_code == 200
        login_data = login_resp.json()
        assert "access_token" in login_data
        token = login_data["access_token"]

        # 5. Access /api/auth/me without token should fail (401)
        unauth_resp = await client.get("/api/auth/me")
        assert unauth_resp.status_code == 401

        # 6. Access /api/auth/me with valid Bearer token should succeed (200)
        me_resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_resp.status_code == 200
        user_info = me_resp.json()
        assert user_info["email"] == test_email
        assert user_info["full_name"] == test_name
        assert "id" in user_info
