import csv
import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

MGR_HEADERS = {"Authorization": "Bearer demo-token-u-manager"}
ADMIN_HEADERS = {"Authorization": "Bearer demo-token-u-admin"}
CREATOR_HEADERS = {"Authorization": "Bearer demo-token-u-creator-social"}


def test_insights_endpoints():
    # 1. Summary
    res = client.get("/api/v1/insights/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["total_reviews"] >= 80
    assert data["synthetic_reviews_count"] >= 80
    assert data["active_governance_rules"] >= 10
    assert "clean_submissions_pct" in data
    assert "avg_findings_per_review" in data

    # 2. Recurring issues
    res = client.get("/api/v1/insights/recurring")
    assert res.status_code == 200
    recurring = res.json()
    assert len(recurring) > 0
    first = recurring[0]
    assert "rule_code" in first
    assert "count" in first
    assert "team_name" in first
    assert "week" in first
    assert "is_synthetic" in first

    # 3. Dismissals breakdown
    res = client.get("/api/v1/insights/dismissals")
    assert res.status_code == 200
    dismissals = res.json()
    assert len(dismissals) > 0
    total_pct = sum(d["percentage"] for d in dismissals)
    assert 98.0 <= total_pct <= 102.0

    # 4. Basic counters per rule
    res = client.get("/api/v1/insights/rules")
    assert res.status_code == 200
    rules = res.json()
    assert len(rules) > 0
    # Ambiguous rule AMBIG-01 should be present with triggers and dismissals
    ambig = next((r for r in rules if "AMBIG" in r["rule_code"]), None)
    assert ambig is not None
    assert ambig["times_triggered"] > 0
    assert ambig["times_dismissed"] > 0
    assert ambig["distinct_dismissers"] >= 1


def test_audit_filters_and_csv_export():
    # 1. Unfiltered audit
    res = client.get("/api/v1/audit", headers=MGR_HEADERS)
    assert res.status_code == 200
    all_logs = res.json()
    assert len(all_logs) > 0

    # 2. Filter by action
    first_action = all_logs[0]["action"]
    res = client.get(f"/api/v1/audit?action={first_action}", headers=MGR_HEADERS)
    assert res.status_code == 200
    filtered = res.json()
    assert all(l["action"] == first_action for l in filtered)

    # 3. Filter by entity_type
    first_entity = all_logs[0]["entity_type"]
    res = client.get(f"/api/v1/audit?entity_type={first_entity}", headers=MGR_HEADERS)
    assert res.status_code == 200
    assert all(l["entity_type"] == first_entity for l in res.json())

    # 4. Creator cannot export or view audit logs
    res = client.get("/api/v1/audit", headers=CREATOR_HEADERS)
    assert res.status_code == 403
    res = client.get("/api/v1/audit/export", headers=CREATOR_HEADERS)
    assert res.status_code == 403

    # 5. Admin and Manager can export CSV
    res = client.get("/api/v1/audit/export", headers=ADMIN_HEADERS)
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "attachment; filename=" in res.headers["content-disposition"]

    # Parse CSV content
    reader = csv.reader(io.StringIO(res.text))
    rows = list(reader)
    assert len(rows) >= 2  # header + at least 1 row
    assert rows[0] == [
        "id",
        "timestamp",
        "actor_id",
        "actor_role",
        "action",
        "entity_type",
        "entity_id",
        "details_json",
        "request_id",
        "prev_hash",
        "hash",
    ]


def test_system_status_endpoint():
    res = client.get("/api/v1/system/status")
    assert res.status_code == 200
    data = res.json()
    assert data["version"] == "0.2.0"
    assert "commit" in data
    assert data["ai_mode"] == "mock"
    assert data["health"] == "healthy"
    assert data["db_connected"] is True
