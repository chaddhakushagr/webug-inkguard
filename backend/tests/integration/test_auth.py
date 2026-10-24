from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def test_auth_login_and_me():
    # 1. Login with demo user Elena
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "creator.social@lumo.internal", "password": settings.DEMO_PASSWORD},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    token = data["access_token"]
    assert data["user"]["email"] == "creator.social@lumo.internal"
    assert data["user"]["role"] == "creator"

    # 2. Access /auth/me with valid Bearer token
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "creator.social@lumo.internal"
    assert me_data["role"] == "creator"


def test_auth_failures_and_401():
    # Missing token
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401

    # Invalid token
    res_bad = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-valid-jwt"})
    assert res_bad.status_code == 401

    # Invalid password
    res_wrong_pw = client.post(
        "/api/v1/auth/login",
        json={"email": "creator.social@lumo.internal", "password": "WrongPassword123!"},
    )
    assert res_wrong_pw.status_code == 401
