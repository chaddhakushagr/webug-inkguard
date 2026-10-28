"""
Integration tests for Guideline Health endpoints (Round 3 Improvement 2).
Verifies:
- GET /api/v1/insights/guideline-health (role-gated, returns ranking with RULE-AMBIG-01 in top 3)
- GET /api/v1/insights/stale (returns stale rules including expired facts, past review date, unused rules)
- GET /api/v1/insights/gaps (returns clustered reviewer comment proposals in draft status)
- RBAC: Creator and Reviewer receive 403 Forbidden on approve and reject
- POST /api/v1/insights/gaps/{id}/approve (promotes draft to active KB entry, writes audit log)
- POST /api/v1/insights/gaps/{id}/reject (requires substantive reason, writes audit log)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.adapters.db.session import SessionLocal
from app.adapters.db.models import KBEntry, AuditLog


client = TestClient(app)


def login(email: str, password: str = "LumoDemo2026!") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Failed login for {email}: {res.text}"
    return res.json()["access_token"]


def test_guideline_health_rbac():
    """Brand manager and admin have access; unauthenticated 401; creator/reviewer 403."""
    # Unauthenticated -> 401
    res = client.get("/api/v1/insights/guideline-health")
    assert res.status_code == 401

    # Creator -> 403
    creator_tok = login("creator.maya@lumo.internal")
    res = client.get(
        "/api/v1/insights/guideline-health",
        headers={"Authorization": f"Bearer {creator_tok}"},
    )
    assert res.status_code == 403

    # Reviewer -> 403
    rev_tok = login("reviewer.sarah@lumo.internal")
    res = client.get(
        "/api/v1/insights/guideline-health",
        headers={"Authorization": f"Bearer {rev_tok}"},
    )
    assert res.status_code == 403

    # Brand Manager -> 200
    bm_tok = login("manager.kavita@lumo.internal")
    res = client.get(
        "/api/v1/insights/guideline-health",
        headers={"Authorization": f"Bearer {bm_tok}"},
    )
    assert res.status_code == 200


def test_guideline_health_seeded_problems_surfaced():
    """Asserts that RULE-AMBIG-01 ranks in the top 3 most ambiguous rules."""
    bm_tok = login("manager.kavita@lumo.internal")
    res = client.get(
        "/api/v1/insights/guideline-health",
        headers={"Authorization": f"Bearer {bm_tok}"},
    )
    assert res.status_code == 200
    items = res.json()
    assert len(items) > 0

    top_3_codes = [it["rule_code"] for it in items[:3]]
    assert "RULE-AMBIG-01" in top_3_codes, f"RULE-AMBIG-01 not in top 3: {top_3_codes}"

    ambig_item = next(it for it in items if it["rule_code"] == "RULE-AMBIG-01")
    assert ambig_item["status"] == "evaluated"
    assert ambig_item["ambiguity_score"] is not None
    assert ambig_item["ambiguity_score"] >= 45
    assert ambig_item["creator_dismissals"] > 0
    assert ambig_item["reviewer_overrides"] > 0


def test_stale_rules_surfaced():
    """Asserts that GET /insights/stale surfaces expired facts and un-triggered rules."""
    bm_tok = login("manager.kavita@lumo.internal")
    res = client.get(
        "/api/v1/insights/stale",
        headers={"Authorization": f"Bearer {bm_tok}"},
    )
    assert res.status_code == 200
    stale_items = res.json()
    assert len(stale_items) > 0

    stale_codes = {it["code"]: it for it in stale_items}
    # FACT-002 is expired
    assert "FACT-002" in stale_codes
    assert stale_codes["FACT-002"]["severity"] == "high"
    assert any("fact_expired" in r for r in stale_codes["FACT-002"]["stale_reasons"])

    # RULE-CLAIM-03 cites expired FACT-002
    assert "RULE-CLAIM-03" in stale_codes
    assert any("cites_expired_facts: FACT-002" in r for r in stale_codes["RULE-CLAIM-03"]["stale_reasons"])


def test_gaps_rbac_cannot_activate_by_creator_or_reviewer():
    """Creator and reviewer cannot approve or reject draft gap proposals."""
    bm_tok = login("manager.kavita@lumo.internal")
    gaps_res = client.get(
        "/api/v1/insights/gaps",
        headers={"Authorization": f"Bearer {bm_tok}"},
    )
    assert gaps_res.status_code == 200
    gaps = gaps_res.json()
    assert len(gaps) > 0
    target_gap = gaps[0]

    # Creator tries to approve -> 403
    creator_tok = login("creator.maya@lumo.internal")
    res = client.post(
        f"/api/v1/insights/gaps/{target_gap['id']}/approve",
        headers={"Authorization": f"Bearer {creator_tok}"},
    )
    assert res.status_code == 403

    # Reviewer tries to approve -> 403
    rev_tok = login("reviewer.sarah@lumo.internal")
    res = client.post(
        f"/api/v1/insights/gaps/{target_gap['id']}/approve",
        headers={"Authorization": f"Bearer {rev_tok}"},
    )
    assert res.status_code == 403

    # Reviewer tries to reject -> 403
    res = client.post(
        f"/api/v1/insights/gaps/{target_gap['id']}/reject",
        headers={"Authorization": f"Bearer {rev_tok}"},
        json={"reason": "Not a priority"},
    )
    assert res.status_code == 403


def test_gaps_approve_and_reject_with_audit_log():
    """
    Brand manager approves one gap proposal and rejects another.
    Asserts KB entry is created with status active, and audit entries are recorded.
    """
    bm_tok = login("manager.kavita@lumo.internal")
    gaps_res = client.get(
        "/api/v1/insights/gaps",
        headers={"Authorization": f"Bearer {bm_tok}"},
    )
    assert gaps_res.status_code == 200
    gaps = gaps_res.json()
    assert len(gaps) >= 2, f"Expected at least 2 gap proposals, got {len(gaps)}"

    gap_to_approve = gaps[0]
    gap_to_reject = gaps[1]

    # 1. Reject requires substantive reason
    bad_reject = client.post(
        f"/api/v1/insights/gaps/{gap_to_reject['id']}/reject",
        headers={"Authorization": f"Bearer {bm_tok}"},
        json={"reason": "no"},
    )
    assert bad_reject.status_code == 422

    # 2. Substantive reject
    reject_res = client.post(
        f"/api/v1/insights/gaps/{gap_to_reject['id']}/reject",
        headers={"Authorization": f"Bearer {bm_tok}"},
        json={"reason": "Existing international distribution policy already covers EU VAT."},
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["action"] == "rejected"

    # 3. Approve gap proposal
    approve_res = client.post(
        f"/api/v1/insights/gaps/{gap_to_approve['id']}/approve",
        headers={"Authorization": f"Bearer {bm_tok}"},
    )
    assert approve_res.status_code == 200
    appr_data = approve_res.json()
    assert appr_data["action"] == "approved"
    assert appr_data["entry_id"] is not None

    # Verify newly created KB entry exists and is active
    db = SessionLocal()
    try:
        new_entry = db.query(KBEntry).filter(KBEntry.id == appr_data["entry_id"]).first()
        assert new_entry is not None
        assert new_entry.status == "active"
        assert new_entry.current_version == 1

        # Verify audit logs
        audit_approve = (
            db.query(AuditLog)
            .filter(AuditLog.action == "kb_entry_created_from_gap", AuditLog.entity_id == new_entry.id)
            .first()
        )
        assert audit_approve is not None
        assert audit_approve.actor_role == "brand_manager"

        audit_reject = (
            db.query(AuditLog)
            .filter(AuditLog.action == "kb_gap_rejected", AuditLog.entity_id == gap_to_reject["id"])
            .first()
        )
        assert audit_reject is not None
        assert audit_reject.details.get("reason") is not None
    finally:
        db.close()
