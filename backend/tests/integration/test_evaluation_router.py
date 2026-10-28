"""
Integration tests for Evaluation Router.
Verifies RBAC protection (brand_manager, admin allowed; creator, reviewer blocked),
data structure, and response format.
"""

from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def get_token(email: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": settings.DEMO_PASSWORD})
    assert res.status_code == 200, f"Failed login for {email}: {res.text}"
    return res.json()["access_token"]


def test_evaluation_results_rbac_and_payload():
    creator_token = get_token("creator.social@lumo.internal")
    reviewer_token = get_token("reviewer.sarah@lumo.internal")
    manager_token = get_token("manager.kavita@lumo.internal")
    admin_token = get_token("admin@lumo.internal")

    # 1. Unauthenticated request returns 401
    res_unauth = client.get("/api/v1/evaluation/results")
    assert res_unauth.status_code == 401

    # 2. Creator role is forbidden (403)
    res_creator = client.get(
        "/api/v1/evaluation/results",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert res_creator.status_code == 403

    # 3. Reviewer role is forbidden (403)
    res_reviewer = client.get(
        "/api/v1/evaluation/results",
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert res_reviewer.status_code == 403

    # 4. Brand Manager role succeeds (200)
    res_manager = client.get(
        "/api/v1/evaluation/results",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert res_manager.status_code == 200
    data = res_manager.json()
    assert "summary" in data
    assert "before_after" in data
    assert "by_issue_type" in data
    assert "false_positives" in data
    assert len(data["before_after"]) >= 2
    assert data["summary"]["total_documents"] == 84
    assert data["summary"]["overall"]["precision"] > 0
    assert data["summary"]["overall"]["recall"] > 0

    # 5. Admin role succeeds on alias route /api/v1/eval/latest (200)
    res_admin = client.get(
        "/api/v1/eval/latest",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == 200
    admin_data = res_admin.json()
    assert admin_data["metadata"]["model"] == settings.LLM_MODEL
