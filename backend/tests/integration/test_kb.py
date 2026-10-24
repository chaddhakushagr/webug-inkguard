from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def get_token(email: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": settings.DEMO_PASSWORD})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_kb_crud_and_versioning():
    manager_token = get_token("manager.kavita@lumo.internal")
    creator_token = get_token("creator.social@lumo.internal")
    agency_token = get_token("creator.agency@contractor.external")  # max_tier: public

    # 1. Creator cannot create KB entries (403 Forbidden)
    res_creator_fail = client.post(
        "/api/v1/kb/entries",
        json={
            "code": "TERM-TEST-01",
            "type": "term",
            "title": "Banned Term Test",
            "body": "Do not use miracle",
            "classification": "internal",
        },
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert res_creator_fail.status_code == 403

    # 2. Manager creates KB entry (version 1)
    import uuid
    code = f"TERM-TEST-{uuid.uuid4().hex[:6].upper()}"
    res_create = client.post(
        "/api/v1/kb/entries",
        json={
            "code": code,
            "type": "term",
            "title": "Banned Term Test",
            "body": "Do not use miracle",
            "classification": "internal",
            "data": {"banned": "miracle", "preferred": "effective"},
        },
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert res_create.status_code == 200
    entry_data = res_create.json()
    assert entry_data["code"] == code
    assert entry_data["current_version"] == 1
    entry_id = entry_data["id"]

    # 3. Manager updates KB entry (creates version 2)
    res_update = client.put(
        f"/api/v1/kb/entries/{entry_id}",
        json={
            "title": "Banned Term Test - Revised",
            "change_note": "Added explanation for skincare compliance",
        },
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert res_update.status_code == 200
    updated_data = res_update.json()
    assert updated_data["current_version"] == 2
    assert updated_data["title"] == "Banned Term Test - Revised"

    # 4. Check version history has both versions
    res_versions = client.get(
        f"/api/v1/kb/entries/{entry_id}/versions",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert res_versions.status_code == 200
    versions = res_versions.json()
    assert len(versions) == 2
    assert versions[0]["version"] == 2
    assert versions[1]["version"] == 1

    # 5. Classification tier boundary: agency creator (max_tier: public) cannot access internal entry
    res_agency_get = client.get(
        f"/api/v1/kb/entries/{entry_id}",
        headers={"Authorization": f"Bearer {agency_token}"},
    )
    assert res_agency_get.status_code == 404
