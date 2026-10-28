"""
Phase 6 Robustness Integration Tests:
1. 30-second timeout wrapper on external calls (LLM, verifier) with safe fallback
   (finding stays with needs_human_judgment=True, no 500 error).
2. Idempotency keys & 60-second duplicate check: submitting same content twice within 60s
   returns existing submission_id, not a duplicate.
3. Daily cap enforcement: falls back to rules_only and returns header X-LLM-Cap-Reached: true.
"""

import time
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.domain.review.models import ReviewContext, FindingItem
from app.domain.review.verifier import LLMVerifierStage
from app.adapters.llm.openai_compatible import execute_with_30s_timeout
from app.seed.lumo_brand import SEED_FACTS

client = TestClient(app)


def get_token(email: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "LumoDemo2026!"})
    assert res.status_code == 200, f"Login failed: {res.text}"
    return res.json()["access_token"]


def test_phase6_30s_timeout_wrapper_and_safe_fallback():
    """
    Phase 6.1:
    - Verifies execute_with_30s_timeout enforces timeout constraint.
    - If verifier call times out, finding stays with needs_human_judgment=True without 500 error.
    """
    # 1. Test timeout wrapper directly with a slow callable
    def slow_func():
        time.sleep(0.5)
        return "done"

    with pytest.raises(TimeoutError, match="exceeded"):
        execute_with_30s_timeout(slow_func, timeout=0.1)

    # 2. Test LLMVerifierStage safe fallback on timeout
    class TimeoutLLMAdapter:
        def verify(self, finding, excerpt, cited_entry, prompt_version="v1"):
            raise TimeoutError("External LLM call exceeded 30s timeout limit.")

    fact_001 = next(f for f in SEED_FACTS if f["code"] == "FACT-001")
    finding = FindingItem(
        id="find-timeout-001",
        source="ai",
        issue_type="claim",
        severity="high",
        confidence=0.85,
        span_start=0,
        span_end=24,
        excerpt="cure dry skin completely",
        explanation="Medical cure claim needing verifier pass",
        cited_entry_code="FACT-001",
        claim_verdict="Contradicted",
        is_policy=True,
    )

    ctx = ReviewContext(
        text="cure dry skin completely in just 3 days.",
        mode="live",
        kb_pool=[fact_001],
        findings=[finding],
    )

    stage = LLMVerifierStage(llm_adapter=TimeoutLLMAdapter(), enabled=True)
    res_ctx = stage.process(ctx)

    # Safe fallback: Finding is NOT dropped, no 500 error raised, and needs_human_judgment is True
    assert len(res_ctx.findings) == 1
    validated = res_ctx.findings[0]
    assert validated.id == "find-timeout-001"
    assert validated.needs_human_judgment is True
    assert validated.verifier_verdict == "unsure"
    assert "timeout" in validated.verifier_reason.lower()


def test_phase6_idempotency_60s_returns_existing_submission():
    """
    Phase 6.2:
    Submitting the same content twice within 60 seconds returns the existing submission_id,
    not a duplicate.
    """
    creator_token = get_token("creator.social@lumo.internal")
    h = {"Authorization": f"Bearer {creator_token}"}

    unique_content = f"Unique marketing copy for idempotency verification {time.time()}"
    payload = {
        "title": "Idempotent Submission Test",
        "channel": "social",
        "content": unique_content,
    }

    # First submission
    res1 = client.post("/api/v1/submissions", json=payload, headers=h)
    assert res1.status_code == 200
    sub1 = res1.json()
    sub_id1 = sub1["id"]

    # Second submission with same content within 60s
    res2 = client.post("/api/v1/submissions", json=payload, headers=h)
    assert res2.status_code == 200
    sub2 = res2.json()
    sub_id2 = sub2["id"]

    # Must return existing submission_id, not a duplicate
    assert sub_id1 == sub_id2

    # Also test with explicit Idempotency-Key header
    h_idem = {**h, "Idempotency-Key": f"key-{time.time()}"}
    res3 = client.post("/api/v1/submissions", json=payload, headers=h_idem)
    assert res3.status_code == 200
    assert res3.json()["id"] == sub_id1


def test_phase6_daily_cap_enforcement_and_header():
    """
    Phase 6.3:
    When LLM_DAILY_CAP is reached, pipeline falls back to rules_only mode
    and returns a header X-LLM-Cap-Reached: true.
    """
    admin_token = get_token("admin@lumo.internal")
    creator_token = get_token("creator.social@lumo.internal")
    h_admin = {"Authorization": f"Bearer {admin_token}"}
    h_creator = {"Authorization": f"Bearer {creator_token}"}

    # Force cap to 0
    client.put("/api/v1/settings", json={"llm_daily_cap": 0}, headers=h_admin)

    try:
        # Create submission
        sub_res = client.post(
            "/api/v1/submissions",
            json={
                "title": f"Cap Enforcement Test {time.time()}",
                "channel": "social",
                "content": "Lumo daily hydration check with cap enforcement.",
            },
            headers=h_creator,
        )
        assert sub_res.status_code == 200
        sub_id = sub_res.json()["id"]

        # Run review (sync mode)
        rev_res = client.post(f"/api/v1/submissions/{sub_id}/review?sync=true", headers=h_creator)
        assert rev_res.status_code == 200

        # Verify header is returned
        assert (
            rev_res.headers.get("x-llm-cap-reached") == "true"
            or rev_res.headers.get("X-LLM-Cap-Reached") == "true"
        )

        rev_data = rev_res.json()
        assert rev_data["status"] == "completed"
        # Mode fell back or fallback_reason is recorded
        fallback = rev_data.get("fallback_reason") or ""
        assert "cap reached" in fallback.lower() or rev_data.get("mode") == "rules_only"

        # Also verify polling GET /reviews/{id} returns the header
        poll_res = client.get(f"/api/v1/reviews/{rev_data['id']}", headers=h_creator)
        assert poll_res.status_code == 200
        assert (
            poll_res.headers.get("x-llm-cap-reached") == "true"
            or poll_res.headers.get("X-LLM-Cap-Reached") == "true"
        )
    finally:
        # Restore daily cap
        client.put("/api/v1/settings", json={"llm_daily_cap": 100}, headers=h_admin)
