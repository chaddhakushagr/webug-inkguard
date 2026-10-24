from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.2.0"
    assert "X-Request-ID" in response.headers


def test_demo_users_endpoint():
    response = client.get("/api/v1/auth/demo-users")
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 4
    roles = {u["role"] for u in users}
    assert "creator" in roles
    assert "reviewer" in roles
    assert "brand_manager" in roles
    assert "admin" in roles


def test_kb_entries_stub():
    # Login as demo user
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "creator.social@lumo.internal", "password": "LumoDemo2026!"},
    )
    token = login_res.json()["access_token"]
    response = client.get(
        "/api/v1/kb/entries",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


def test_submissions_and_findings_stubs():
    response = client.get("/api/v1/submissions")
    assert response.status_code == 200
    subs = response.json()
    assert len(subs) >= 1
    sub_id = subs[0]["id"]

    findings_res = client.get(f"/api/v1/submissions/{sub_id}/findings")
    assert findings_res.status_code == 200
    findings = findings_res.json()
    assert len(findings) >= 2


def test_error_envelope_format():
    response = client.get("/api/v1/non-existent-endpoint")
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "HTTP_404"
    assert "message" in data
    assert "details" in data
