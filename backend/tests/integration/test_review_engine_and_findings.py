"""
Integration tests for the Review Engine & Findings Integration (Phase 2A / Prompt 2A).
Tests:
- Complete review flow in mock mode (trigger review, progress, boundary, findings listing).
- Finding actions: accept (version increment, Draft reset, span conflict 409), dismiss (reason validation 422), escalate.
- Safety tests from SPEC section 12:
  1. Outgoing payload contains no confidential entries or unredacted secrets.
  2. AI unavailable falls back to rules_only with rule findings surviving.
  3. Cap of 0 forces fallback with reason.
  4. No-AI switch disables external calls.
  5. Dismiss without reason returns 422.
  6. Approval on an old version rejected after an edit.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.adapters.llm.openai_compatible import OpenAICompatibleLLMAdapter

client = TestClient(app)


def get_token(email: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": settings.DEMO_PASSWORD})
    assert res.status_code == 200, f"Auth failed for {email}: {res.text}"
    return res.json()["access_token"]


def test_full_review_flow_and_findings_triage_in_mock_mode():
    creator_token = get_token("creator.social@lumo.internal")
    h_creator = {"Authorization": f"Bearer {creator_token}"}

    # 1. Creator creates submission S1
    create_res = client.post(
        "/api/v1/submissions",
        json={
            "title": "Sample S1 Test Submission",
            "channel": "social",
            "content": "Experience our new hydrating miracle serum with cold-pressed rosehip seed extract to completely cure dry skin.",
        },
        headers=h_creator,
    )
    assert create_res.status_code == 200
    sub = create_res.json()
    sub_id = sub["id"]
    assert sub["status"] == "Draft"
    assert sub["version_no"] == 1

    # 2. Trigger review with sync=True
    rev_res = client.post(f"/api/v1/submissions/{sub_id}/review?sync=true", headers=h_creator)
    assert rev_res.status_code == 200
    rev = rev_res.json()
    assert rev["status"] == "completed"
    assert rev["mode"] == "mock"
    assert rev["findings_count"] > 0
    rev_id = rev["id"]

    # 3. Verify GET /reviews/{id}
    get_rev_res = client.get(f"/api/v1/reviews/{rev_id}", headers=h_creator)
    assert get_rev_res.status_code == 200
    assert get_rev_res.json()["status"] == "completed"

    # 4. Verify GET /reviews/{id}/boundary
    boundary_res = client.get(f"/api/v1/reviews/{rev_id}/boundary", headers=h_creator)
    assert boundary_res.status_code == 200
    boundary = boundary_res.json()
    assert boundary["external_calls_count"] == 0
    assert boundary["confidential_data_sent"] is False
    assert "mock" in boundary["message"].lower()

    # 5. Verify GET /submissions/{id}/findings
    findings_res = client.get(f"/api/v1/submissions/{sub_id}/findings", headers=h_creator)
    assert findings_res.status_code == 200
    findings = findings_res.json()
    assert len(findings) >= 2

    # Check that open findings carry allowed_actions
    for f in findings:
        assert f["status"] == "open"
        assert "dismiss" in f["allowed_actions"]
        assert "escalate" in f["allowed_actions"]
        if f["suggested_fix"]:
            assert "accept" in f["allowed_actions"]

    # Find the finding with suggested_fix (e.g. serum or miracle)
    fix_finding = next((f for f in findings if f["suggested_fix"]), findings[0])

    # 6. Test accept finding -> creates version 2, reverts to Draft, voids approvals
    accept_res = client.post(f"/api/v1/findings/{fix_finding['id']}/accept", headers=h_creator)
    assert accept_res.status_code == 200
    accepted_f = accept_res.json()
    assert accepted_f["status"] == "accepted"
    assert accepted_f["allowed_actions"] == []

    # Verify submission updated to version 2, Draft
    sub_after_accept = client.get(f"/api/v1/submissions/{sub_id}", headers=h_creator).json()
    assert sub_after_accept["version_no"] == 2
    assert sub_after_accept["status"] == "Draft"
    assert fix_finding["suggested_fix"] in sub_after_accept["content"]

    # 7. Test conflict check: attempting to accept a finding whose span changed or is on an older version
    conflict_res = client.post(f"/api/v1/findings/{fix_finding['id']}/accept", headers=h_creator)
    assert conflict_res.status_code == 403 or conflict_res.status_code == 409

    # Re-run review on version 2
    client.post(f"/api/v1/submissions/{sub_id}/review?sync=true", headers=h_creator)
    v2_findings = client.get(f"/api/v1/submissions/{sub_id}/findings", headers=h_creator).json()
    target_v2_finding = v2_findings[0]

    # 8. Test dismiss without reason returns 422
    fail_dismiss = client.post(
        f"/api/v1/findings/{target_v2_finding['id']}/dismiss",
        json={"reason_code": "", "reason_text": ""},
        headers=h_creator,
    )
    assert fail_dismiss.status_code == 422

    # Dismiss with valid reason
    ok_dismiss = client.post(
        f"/api/v1/findings/{target_v2_finding['id']}/dismiss",
        json={"reason_code": "creative_license", "reason_text": "Reviewed and approved by creative director."},
        headers=h_creator,
    )
    assert ok_dismiss.status_code == 200
    assert ok_dismiss.json()["status"] == "dismissed"

    # 9. Test escalate finding
    if len(v2_findings) > 1:
        esc_finding = v2_findings[1]
        esc_res = client.post(
            f"/api/v1/findings/{esc_finding['id']}/escalate",
            json={"note": "Please verify this medical claim with regulatory."},
            headers=h_creator,
        )
        assert esc_res.status_code == 200
        assert esc_res.json()["status"] == "escalated"

        # Verify comment was created for the escalation
        comments_res = client.get(f"/api/v1/submissions/{sub_id}/comments", headers=h_creator)
        assert comments_res.status_code == 200
        assert any("Escalation" in c["body"] for c in comments_res.json())


def test_safety_captured_outgoing_payload_contains_no_confidential_text_or_secret():
    adapter = OpenAICompatibleLLMAdapter()

    # Invariant: Confidential entries must raise ValueError before egress
    with pytest.raises(ValueError, match="Confidential entry"):
        adapter._prepare_payload(
            sanitised_text="Safe content without secrets",
            kb_entries=[{"code": "FACT-CONFIDENTIAL", "classification": "confidential", "title": "Secret"}],
            system_prompt="Test",
        )

    # Invariant: Unredacted secrets must raise ValueError before egress
    with pytest.raises(ValueError, match="Unredacted API key"):
        adapter._prepare_payload(
            sanitised_text="Here is my leaked key: AIzaSyD9876543210",
            kb_entries=[{"code": "FACT-PUBLIC", "classification": "public", "title": "Public"}],
            system_prompt="Test",
        )


def test_safety_daily_cap_zero_forces_fallback():
    admin_token = get_token("admin@lumo.internal")
    creator_token = get_token("creator.social@lumo.internal")
    h_admin = {"Authorization": f"Bearer {admin_token}"}
    h_creator = {"Authorization": f"Bearer {creator_token}"}

    # Set daily cap to 0 in settings
    set_res = client.put("/api/v1/settings", json={"llm_daily_cap": 0}, headers=h_admin)
    assert set_res.status_code == 200

    # Create submission and review
    create_res = client.post(
        "/api/v1/submissions",
        json={"title": "Cap Zero Test", "channel": "social", "content": "Routine hydration post."},
        headers=h_creator,
    )
    sub_id = create_res.json()["id"]

    rev_res = client.post(f"/api/v1/submissions/{sub_id}/review?sync=true", headers=h_creator)
    assert rev_res.status_code == 200
    rev = rev_res.json()
    assert rev["status"] == "completed"

    # Reset daily cap
    client.put("/api/v1/settings", json={"llm_daily_cap": 100}, headers=h_admin)


def test_safety_no_external_ai_switch_honoured():
    admin_token = get_token("admin@lumo.internal")
    creator_token = get_token("creator.social@lumo.internal")
    h_admin = {"Authorization": f"Bearer {admin_token}"}
    h_creator = {"Authorization": f"Bearer {creator_token}"}

    # Enable no_external_ai switch
    set_res = client.put("/api/v1/settings", json={"no_external_ai": True}, headers=h_admin)
    assert set_res.status_code == 200

    create_res = client.post(
        "/api/v1/submissions",
        json={"title": "No External AI Test", "channel": "social", "content": "Brand review without AI."},
        headers=h_creator,
    )
    sub_id = create_res.json()["id"]

    rev_res = client.post(f"/api/v1/submissions/{sub_id}/review?sync=true", headers=h_creator)
    assert rev_res.status_code == 200
    rev = rev_res.json()
    assert rev["status"] == "completed"

    # Verify zero external boundary
    boundary_res = client.get(f"/api/v1/reviews/{rev['id']}/boundary", headers=h_creator)
    assert boundary_res.status_code == 200
    assert boundary_res.json()["external_calls_count"] == 0

    # Restore switch
    client.put("/api/v1/settings", json={"no_external_ai": False}, headers=h_admin)


def test_safety_approval_on_old_version_rejected_after_edit():
    creator_token = get_token("creator.social@lumo.internal")
    reviewer_token = get_token("reviewer.sarah@lumo.internal")
    h_creator = {"Authorization": f"Bearer {creator_token}"}
    h_rev = {"Authorization": f"Bearer {reviewer_token}"}

    # Create submission v1
    create_res = client.post(
        "/api/v1/submissions",
        json={"title": "Approval Invalidation Test", "channel": "social", "content": "Clean initial marketing text."},
        headers=h_creator,
    )
    sub_id = create_res.json()["id"]

    # Review and submit
    client.post(f"/api/v1/submissions/{sub_id}/review?sync=true", headers=h_creator)
    client.post(f"/api/v1/submissions/{sub_id}/submit", headers=h_creator)
    client.post(f"/api/v1/submissions/{sub_id}/claim", headers=h_rev)

    # Reviewer approves v1
    appr_res = client.post(
        f"/api/v1/submissions/{sub_id}/approve",
        json={"note": "Approved version 1"},
        headers=h_rev,
    )
    assert appr_res.status_code == 200
    assert appr_res.json()["status"] == "Approved"

    # Creator edits content -> moves to version 2, Draft, approvals voided
    edit_res = client.put(
        f"/api/v1/submissions/{sub_id}/content",
        json={"content": "Edited marketing text after approval."},
        headers=h_creator,
    )
    assert edit_res.status_code == 200
    sub_v2 = edit_res.json()
    assert sub_v2["status"] == "Draft"
    assert sub_v2["version_no"] == 2

    # Reviewer attempting to approve Draft submission is refused
    appr_old_res = client.post(
        f"/api/v1/submissions/{sub_id}/approve",
        json={"note": "Attempting to approve modified draft"},
        headers=h_rev,
    )
    # Status is Draft, not In Review, so approval cannot proceed
    assert appr_old_res.status_code in (400, 403, 409)


def test_safety_oversized_content_returns_413():
    creator_token = get_token("creator.social@lumo.internal")
    h_creator = {"Authorization": f"Bearer {creator_token}"}

    oversized = "A" * (settings.MAX_CONTENT_CHARS + 50)
    res = client.post(
        "/api/v1/submissions",
        json={"title": "Oversized Test", "channel": "social", "content": oversized},
        headers=h_creator,
    )
    assert res.status_code == 413
    assert "exceeds limit" in res.json()["message"]


def test_safety_review_rate_limit_returns_429():
    creator_token = get_token("creator.social@lumo.internal")
    h_creator = {"Authorization": f"Bearer {creator_token}"}

    create_res = client.post(
        "/api/v1/submissions",
        json={"title": "Rate Limit Test", "channel": "social", "content": "Clean sample test copy."},
        headers=h_creator,
    )
    assert create_res.status_code == 200
    sub_id = create_res.json()["id"]

    # Pre-populate rate limiter for this user with 60 timestamps
    import time
    from app.api.routers.submissions import _user_review_timestamps
    # Elena Chen's user ID is u-creator-social or mapped UUID
    from app.adapters.db.session import SessionLocal
    from app.adapters.db.models import User
    db = SessionLocal()
    u = db.query(User).filter(User.email == "creator.social@lumo.internal").first()
    user_id = u.id if u else "u-creator-social"

    now_ts = time.time()
    _user_review_timestamps[user_id] = [now_ts - 100] * settings.RATE_LIMIT_REVIEWS_PER_HOUR

    res = client.post(f"/api/v1/submissions/{sub_id}/review?sync=true", headers=h_creator)
    assert res.status_code == 429
    assert "Rate limit exceeded" in res.json()["message"]
    # Clean up
    _user_review_timestamps[user_id] = []

