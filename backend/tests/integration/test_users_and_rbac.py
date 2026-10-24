from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def get_token(email: str):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": settings.DEMO_PASSWORD})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_rbac_user_management():
    creator_token = get_token("creator.social@lumo.internal")
    admin_token = get_token("admin@lumo.internal")

    # 1. Creator cannot create users (403 Forbidden)
    res_creator_fail = client.post(
        "/api/v1/users",
        json={
            "email": "unauthorized.user@lumo.internal",
            "name": "Test Unauthorized",
            "role": "creator",
            "max_tier": "internal",
        },
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert res_creator_fail.status_code == 403

    # 2. Admin can create users (200 OK)
    res_admin_success = client.post(
        "/api/v1/users",
        json={
            "email": "new.contractor@lumo.internal",
            "name": "New Contractor",
            "role": "creator",
            "max_tier": "public",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin_success.status_code == 200
    data = res_admin_success.json()
    assert data["email"] == "new.contractor@lumo.internal"
    assert data["role"] == "creator"
    assert data["max_tier"] == "public"

    # 3. Invalid role rejected (422 Unprocessable)
    res_invalid_role = client.post(
        "/api/v1/users",
        json={
            "email": "bad.role@lumo.internal",
            "name": "Bad Role",
            "role": "superman",
            "max_tier": "internal",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_invalid_role.status_code == 422
