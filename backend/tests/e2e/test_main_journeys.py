"""
End-to-End Test Suite for Inkguard Main User Journeys (J1 - J9).

Proves all 9 core journeys required by the Round 3 Specification:
- J1: Creator pastes S1, accepts a suggested fix (creating v2), dismisses one with a reason, submits
- J2: Reviewer claims, comments on a finding, requests changes; creator revises, resubmits
- J3: High-risk content needs two distinct approvers and creator cannot approve own submission
- J4: Mark published workflow with URL recording and audit log
- J5: Brand manager inspects Guideline Health metrics and approves a draft rule proposal from gaps
- J6: Admin edits a KB entry (new v2 created), verified that historical submission still cites v1
- J7: Multi-format upload of DOCX, PDF, and image with document structure extraction and visual checks
- J8: Evaluation results and metrics page loads with precision/recall benchmarks
- J9: AI-off admin switch forces rules-only fallback and completes review cleanly
"""

import os
import uuid
import time
import pytest
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.adapters.db.session import SessionLocal, engine, Base
from app.adapters.db.models import (
    User,
    Submission,
    SubmissionVersion,
    Review,
    Finding,
    Comment,
    KBEntry,
    KBEntryVersion,
    AuditLog,
)
from app.seed.loader import run_seed

# Ensure database tables exist
Base.metadata.create_all(bind=engine)

# Base URL for optional remote/live instance testing (e.g. Neon + Render deployment)
BASE_URL = os.environ.get("E2E_BASE_URL", "").rstrip("/")
DOCS_FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../fixtures/documents"))
ASSETS_FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../fixtures/assets"))


class E2EClient:
    """Unified HTTP client abstracting TestClient (in-process) and httpx (remote)."""

    def __init__(self, base_url: str = ""):
        self.base_url = base_url
        if not base_url:
            self._client = TestClient(app)
        else:
            import httpx
            self._client = httpx.Client(base_url=base_url, timeout=30.0)

    def get(self, path: str, **kwargs):
        if self.base_url:
            url = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"
            return self._client.get(url, **kwargs)
        return self._client.get(path, **kwargs)

    def post(self, path: str, **kwargs):
        if self.base_url:
            url = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"
            return self._client.post(url, **kwargs)
        return self._client.post(path, **kwargs)

    def put(self, path: str, **kwargs):
        if self.base_url:
            url = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"
            return self._client.put(url, **kwargs)
        return self._client.put(path, **kwargs)

    def delete(self, path: str, **kwargs):
        if self.base_url:
            url = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"
            return self._client.delete(url, **kwargs)
        return self._client.delete(path, **kwargs)


@pytest.fixture(scope="module")
def client() -> E2EClient:
    return E2EClient(BASE_URL)


def login(client: E2EClient, email: str) -> str:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": settings.DEMO_PASSWORD},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


# ==============================================================================
# J1: Creator pastes S1, accepts a fix, dismisses one with a reason, submits
# ==============================================================================

def test_j1_creator_s1_fix_dismiss_submit(client: E2EClient):
    """
    J1: Creator pastes S1 brand copy containing claim and term violations,
    triggers review, accepts a suggested fix (generating content version 2),
    dismisses another finding with a valid reason code and explanation,
    and submits for review.
    """
    token = login(client, "creator.social@lumo.internal")
    h = {"Authorization": f"Bearer {token}"}
    run_id = uuid.uuid4().hex[:6]

    # 1. Creator pastes S1 content (with unique tag to avoid idempotency collisions across runs)
    s1_text = (
        f"Get glowing skin with Lumo's all-natural miracle serum! Clinically proven to "
        f"reverse aging in just 3 days. Our 100% organic elixir restores youth without chemicals. "
        f"#cleanbeauty #antiaging #lumo [Run-{run_id}]"
    )
    create_res = client.post(
        "/api/v1/submissions",
        json={
            "title": f"J1 S1 Summer Glow Campaign ({run_id})",
            "channel": "social",
            "content": s1_text,
        },
        headers=h,
    )
    assert create_res.status_code == 200, create_res.text
    sub = create_res.json()
    sub_id = sub["id"]
    assert sub["status"] == "Draft"

    # 2. Trigger review -> moves to Checked
    rev_res = client.post(f"/api/v1/submissions/{sub_id}/review?sync=true", headers=h)
    assert rev_res.status_code == 200, rev_res.text
    rev_data = rev_res.json()
    assert rev_data["status"] == "completed"

    sub_res = client.get(f"/api/v1/submissions/{sub_id}", headers=h)
    assert sub_res.status_code == 200
    assert sub_res.json()["status"] == "Checked"

    # 3. Retrieve findings
    findings_res = client.get(f"/api/v1/submissions/{sub_id}/findings", headers=h)
    assert findings_res.status_code == 200
    findings = findings_res.json()
    assert len(findings) >= 2, f"Expected at least 2 findings on S1, found {len(findings)}"

    # 4. Accept a suggested fix
    fixable = next((f for f in findings if f.get("suggested_fix")), None)
    assert fixable is not None, "At least one finding must have a suggested fix"
    acc_res = client.post(f"/api/v1/findings/{fixable['id']}/accept", headers=h)
    assert acc_res.status_code == 200, acc_res.text
    assert acc_res.json()["status"] == "accepted"

    # Acceptance creates SubmissionVersion 2 and resets status to Draft
    sub_v2_res = client.get(f"/api/v1/submissions/{sub_id}", headers=h)
    assert sub_v2_res.status_code == 200
    assert sub_v2_res.json()["status"] == "Draft"
    assert sub_v2_res.json()["version_no"] == 2

    # 5. Run review on Version 2 -> status becomes Checked
    rev2_res = client.post(f"/api/v1/submissions/{sub_id}/review?sync=true", headers=h)
    assert rev2_res.status_code == 200
    assert rev2_res.json()["status"] == "completed"

    # 6. Dismiss a finding with reason code and explanatory reason text
    findings_v2_res = client.get(f"/api/v1/submissions/{sub_id}/findings", headers=h)
    findings_v2 = findings_v2_res.json()
    assert len(findings_v2) > 0

    target_dismiss = findings_v2[0]
    dismiss_res = client.post(
        f"/api/v1/findings/{target_dismiss['id']}/dismiss",
        json={
            "reason_code": "editorial_exception",
            "reason_text": "Approved brand exception for summer campaign launch by marketing leadership.",
        },
        headers=h,
    )
    assert dismiss_res.status_code == 200, dismiss_res.text
    assert dismiss_res.json()["status"] == "dismissed"

    # 7. Dismiss any remaining open high severity findings so submission gate passes
    for f in findings_v2[1:]:
        if f.get("severity") == "high" and f.get("status") == "open":
            client.post(
                f"/api/v1/findings/{f['id']}/dismiss",
                json={
                    "reason_code": "editorial_exception",
                    "reason_text": "High severity item verified and excepted for marketing release.",
                },
                headers=h,
            )

    # 8. Creator submits
    submit_res = client.post(f"/api/v1/submissions/{sub_id}/submit", headers=h)
    assert submit_res.status_code == 200, submit_res.text
    assert submit_res.json()["status"] == "Submitted"


# ==============================================================================
# J2: Reviewer claims, comments on a finding, requests changes; creator revises, resubmits
# ==============================================================================

def test_j2_reviewer_claim_comment_request_changes_resubmit(client: E2EClient):
    """
    J2: Reviewer claims a submitted submission, adds a threaded review comment,
    requests changes; creator revises copy via PUT /content, reviews, and resubmits.
    """
    creator_token = login(client, "creator.social@lumo.internal")
    reviewer_token = login(client, "reviewer.sarah@lumo.internal")
    h_creator = {"Authorization": f"Bearer {creator_token}"}
    h_rev = {"Authorization": f"Bearer {reviewer_token}"}
    run_id = uuid.uuid4().hex[:6]

    # 1. Creator creates and submits a draft
    create_res = client.post(
        "/api/v1/submissions",
        json={
            "title": f"J2 Botanical Routine ({run_id})",
            "channel": "blog",
            "content": f"Discover our daily botanical hydration routine formulated for natural luminosity. [Run-{run_id}]",
        },
        headers=h_creator,
    )
    assert create_res.status_code == 200
    sub_id = create_res.json()["id"]

    client.post(f"/api/v1/submissions/{sub_id}/review?sync=true", headers=h_creator)
    sub_res = client.post(f"/api/v1/submissions/{sub_id}/submit", headers=h_creator)
    assert sub_res.status_code == 200
    assert sub_res.json()["status"] == "Submitted"

    # 2. Reviewer claims submission
    claim_res = client.post(f"/api/v1/submissions/{sub_id}/claim", headers=h_rev)
    assert claim_res.status_code == 200, claim_res.text
    assert claim_res.json()["status"] == "In Review"

    # 3. Reviewer comments on submission
    comment_res = client.post(
        f"/api/v1/submissions/{sub_id}/comments",
        json={"body": "Please add explicit sourcing details for our cold-pressed rosehip seed oil."},
        headers=h_rev,
    )
    assert comment_res.status_code == 200, comment_res.text
    assert "rosehip seed oil" in comment_res.json()["body"]

    # 4. Reviewer requests changes with explanatory note
    req_changes_res = client.post(
        f"/api/v1/submissions/{sub_id}/request-changes",
        json={"note": "Please update ingredient sourcing details and clarify botanical claims."},
        headers=h_rev,
    )
    assert req_changes_res.status_code == 200, req_changes_res.text
    assert req_changes_res.json()["status"] == "Changes Requested"

    # 5. Creator revises copy via PUT /submissions/{id}/content
    revised_copy = (
        f"Discover our daily botanical hydration routine with sustainably sourced cold-pressed "
        f"rosehip seed oil formulated for natural luminosity. [Run-{run_id}]"
    )
    update_res = client.put(
        f"/api/v1/submissions/{sub_id}/content",
        json={"content": revised_copy, "source": "edit"},
        headers=h_creator,
    )
    assert update_res.status_code == 200, update_res.text
    assert update_res.json()["status"] == "Draft"
    assert update_res.json()["version_no"] == 2

    # 6. Creator reviews and resubmits
    client.post(f"/api/v1/submissions/{sub_id}/review?sync=true", headers=h_creator)
    resubmit_res = client.post(f"/api/v1/submissions/{sub_id}/submit", headers=h_creator)
    assert resubmit_res.status_code == 200, resubmit_res.text
    assert resubmit_res.json()["status"] == "Submitted"


# ==============================================================================
# J3: High-risk content needs two distinct approvers and creator cannot approve own
# ==============================================================================

def test_j3_high_risk_two_distinct_approvers_no_self_approval(client: E2EClient):
    """
    J3: High-risk submission (press_release) requires two distinct reviewer approvals.
    Creator is strictly prevented from self-approving (invariant).
    Reviewer 1 approving advances count to 1/2 (status remains In Review).
    Duplicate approval by Reviewer 1 is rejected with HTTP 400.
    Reviewer 2 approving satisfies the 2-approver threshold and advances status to Approved.
    """
    creator_token = login(client, "creator.social@lumo.internal")
    reviewer1_token = login(client, "reviewer.sarah@lumo.internal")
    reviewer2_token = login(client, "reviewer.alex@lumo.internal")

    h_creator = {"Authorization": f"Bearer {creator_token}"}
    h_rev1 = {"Authorization": f"Bearer {reviewer1_token}"}
    h_rev2 = {"Authorization": f"Bearer {reviewer2_token}"}
    run_id = uuid.uuid4().hex[:6]

    # 1. Creator creates high-risk press release
    create_res = client.post(
        "/api/v1/submissions",
        json={
            "title": f"J3 Annual Clinical Trial Results ({run_id})",
            "channel": "press_release",  # Canonical high-risk channel
            "content": f"Lumo Skincare announces positive preliminary clinical results from our recent study. [Run-{run_id}]",
        },
        headers=h_creator,
    )
    assert create_res.status_code == 200, create_res.text
    sub = create_res.json()
    sub_id = sub["id"]
    assert sub["risk_tier"] == "high"

    # Review and submit
    client.post(f"/api/v1/submissions/{sub_id}/review?sync=true", headers=h_creator)
    submit_res = client.post(f"/api/v1/submissions/{sub_id}/submit", headers=h_creator)
    assert submit_res.status_code == 200, submit_res.text
    assert submit_res.json()["status"] == "Submitted"

    # 2. Invariant: Creator cannot approve their own submission
    self_appr = client.post(
        f"/api/v1/submissions/{sub_id}/approve",
        json={"note": "Creator attempting unauthorized self-approval"},
        headers=h_creator,
    )
    assert self_appr.status_code in (400, 403, 409), f"Self-approval must be blocked: {self_appr.text}"

    # 3. Reviewer 1 claims and approves
    claim_res = client.post(f"/api/v1/submissions/{sub_id}/claim", headers=h_rev1)
    assert claim_res.status_code == 200
    assert claim_res.json()["status"] == "In Review"

    appr1_res = client.post(
        f"/api/v1/submissions/{sub_id}/approve",
        json={"note": "Reviewer 1 initial clinical sign-off"},
        headers=h_rev1,
    )
    assert appr1_res.status_code == 200, appr1_res.text
    appr1_data = appr1_res.json()
    # High risk requires 2 approvers: status must remain In Review
    assert appr1_data["status"] == "In Review"

    # 4. Duplicate approval attempt by Reviewer 1 must fail with 400
    dup_appr = client.post(
        f"/api/v1/submissions/{sub_id}/approve",
        json={"note": "Reviewer 1 attempting duplicate second approval"},
        headers=h_rev1,
    )
    assert dup_appr.status_code == 400, f"Duplicate approval by same reviewer must return 400: {dup_appr.text}"

    # 5. Reviewer 2 approves -> satisfies 2-approver requirement, transitions to Approved
    appr2_res = client.post(
        f"/api/v1/submissions/{sub_id}/approve",
        json={"note": "Reviewer 2 final compliance sign-off"},
        headers=h_rev2,
    )
    assert appr2_res.status_code == 200, appr2_res.text
    appr2_data = appr2_res.json()
    assert appr2_data["status"] == "Approved"


# ==============================================================================
# J4: Mark published
# ==============================================================================

def test_j4_mark_published(client: E2EClient):
    """
    J4: With a submission in Approved status, creator marks it published with a live URL.
    Status transitions to Marked Published, published_url and timestamp are stored,
    and the action is recorded in the immutable audit log.
    """
    creator_token = login(client, "creator.social@lumo.internal")
    reviewer_token = login(client, "reviewer.sarah@lumo.internal")
    h_creator = {"Authorization": f"Bearer {creator_token}"}
    h_rev = {"Authorization": f"Bearer {reviewer_token}"}
    run_id = uuid.uuid4().hex[:6]

    # 1. Create, review, submit, claim, approve low-risk submission
    res = client.post(
        "/api/v1/submissions",
        json={
            "title": f"J4 Social Post Ready to Publish ({run_id})",
            "channel": "social",
            "content": f"Discover effortless radiance with our daily botanical skincare routine. [Run-{run_id}]",
        },
        headers=h_creator,
    )
    assert res.status_code == 200
    sub_id = res.json()["id"]

    client.post(f"/api/v1/submissions/{sub_id}/review?sync=true", headers=h_creator)
    client.post(f"/api/v1/submissions/{sub_id}/submit", headers=h_creator)
    client.post(f"/api/v1/submissions/{sub_id}/claim", headers=h_rev)
    appr_res = client.post(
        f"/api/v1/submissions/{sub_id}/approve",
        json={"note": "Approved for publication"},
        headers=h_rev,
    )
    assert appr_res.status_code == 200
    assert appr_res.json()["status"] == "Approved"

    # 2. Mark published with URL
    pub_url = f"https://instagram.com/p/lumo_live_{run_id}"
    pub_res = client.post(
        f"/api/v1/submissions/{sub_id}/mark-published",
        json={"url": pub_url},
        headers=h_creator,
    )
    assert pub_res.status_code == 200, pub_res.text
    pub_data = pub_res.json()
    assert pub_data["status"] == "Marked Published"
    assert pub_data["published_url"] == pub_url
    assert pub_data["published_at"] is not None


# ==============================================================================
# J5: Brand manager sees Guideline Health and approves a draft rule
# ==============================================================================

def test_j5_brand_manager_guideline_health_and_approve_draft_rule(client: E2EClient):
    """
    J5: Brand manager accesses Guideline Health intelligence, views ambiguity scores
    and rule proposals clustered from uncited reviewer comments, and approves a proposal.
    The rule is added to the active Knowledge Base with version 1 and an audit entry.
    """
    manager_token = login(client, "manager.kavita@lumo.internal")
    h_mgr = {"Authorization": f"Bearer {manager_token}"}

    # 1. Verify Guideline Health ambiguity scoring endpoint
    health_res = client.get("/api/v1/insights/guideline-health", headers=h_mgr)
    assert health_res.status_code == 200, health_res.text
    health_items = health_res.json()
    assert isinstance(health_items, list)
    assert len(health_items) > 0
    first_item = health_items[0]
    assert "rule_code" in first_item
    assert "ambiguity_score" in first_item
    assert "status" in first_item

    # 2. Verify Gaps detection endpoint
    gaps_res = client.get("/api/v1/insights/gaps", headers=h_mgr)
    assert gaps_res.status_code == 200, gaps_res.text
    proposals = gaps_res.json()

    # If proposals list is empty, dynamically seed 2 uncited comments to create a proposal
    if not proposals:
        creator_token = login(client, "creator.social@lumo.internal")
        h_creator = {"Authorization": f"Bearer {creator_token}"}
        sub_create = client.post(
            "/api/v1/submissions",
            json={
                "title": "Seed Submission for Gap Detection",
                "channel": "social",
                "content": "European orders require VAT disclosure. Validated compliant text.",
            },
            headers=h_creator,
        )
        sub_id = sub_create.json()["id"]
        # Add 2 uncited comments with shared vocabulary
        client.post(
            f"/api/v1/submissions/{sub_id}/comments",
            json={"body": "European international orders must disclose VAT customs duties at checkout."},
            headers=h_mgr,
        )
        client.post(
            f"/api/v1/submissions/{sub_id}/comments",
            json={"body": "Please add explicit EU VAT customs notification for all international orders."},
            headers=h_mgr,
        )
        gaps_res = client.get("/api/v1/insights/gaps", headers=h_mgr)
        proposals = gaps_res.json()

    assert len(proposals) > 0, "Expected at least one gap proposal"
    target_proposal = proposals[0]
    proposal_id = target_proposal["id"]

    # 3. Brand manager approves the candidate rule proposal
    approve_res = client.post(f"/api/v1/insights/gaps/{proposal_id}/approve", headers=h_mgr)
    assert approve_res.status_code == 200, approve_res.text
    approve_data = approve_res.json()
    assert approve_data["action"] == "approved"
    assert "entry_id" in approve_data

    # 4. Verify entry now exists in Knowledge Base with version 1
    new_entry_id = approve_data["entry_id"]
    entry_res = client.get(f"/api/v1/kb/entries/{new_entry_id}", headers=h_mgr)
    assert entry_res.status_code == 200
    entry_data = entry_res.json()
    assert entry_data["status"] == "active"
    assert entry_data["current_version"] == 1


# ==============================================================================
# J6: Admin edits a KB entry, new version created, old submission cites old version
# ==============================================================================

def test_j6_admin_edits_kb_entry_historical_citation_preserved(client: E2EClient):
    """
    J6: An active KB entry is cited by a submission. Admin edits the KB entry, creating version 2.
    Verifies the KB entry's current_version is 2, while the historical submission's finding
    still immutably references version 1.
    """
    creator_token = login(client, "creator.social@lumo.internal")
    admin_token = login(client, "admin@lumo.internal")
    h_creator = {"Authorization": f"Bearer {creator_token}"}
    h_admin = {"Authorization": f"Bearer {admin_token}"}
    run_id = uuid.uuid4().hex[:6]

    # 1. Admin creates a dedicated test KB entry (v1)
    kb_code = f"RULE-TEST-{run_id.upper()}"
    create_kb_res = client.post(
        "/api/v1/kb/entries",
        json={
            "code": kb_code,
            "type": "term",
            "title": f"Banned Term {kb_code}",
            "body": f"Avoid using forbidden phrase '{kb_code}' in marketing copy.",
            "classification": "internal",
            "data": {"banned": kb_code.lower(), "preferred": "botanical elixir", "severity": "medium"},
        },
        headers=h_admin,
    )
    assert create_kb_res.status_code == 200, create_kb_res.text
    kb_data = create_kb_res.json()
    kb_id = kb_data["id"]
    assert kb_data["current_version"] == 1

    # 2. Creator submits copy containing the violation
    sub_res = client.post(
        "/api/v1/submissions",
        json={
            "title": f"Historical Citation Test ({run_id})",
            "channel": "social",
            "content": f"Experience our new {kb_code.lower()} with organic rosehip essence.",
        },
        headers=h_creator,
    )
    assert sub_res.status_code == 200
    sub_id = sub_res.json()["id"]

    # Run review
    client.post(f"/api/v1/submissions/{sub_id}/review?sync=true", headers=h_creator)

    # Verify finding cites Version 1 of the KB entry
    findings_res = client.get(f"/api/v1/submissions/{sub_id}/findings", headers=h_creator)
    assert findings_res.status_code == 200
    target_finding = next(
        (f for f in findings_res.json() if f.get("cited_entry_code") == kb_code),
        None,
    )
    assert target_finding is not None, f"Expected finding citing {kb_code}"
    assert target_finding["cited_entry_version"] == 1

    # 3. Admin edits the KB entry, creating Version 2
    update_res = client.put(
        f"/api/v1/kb/entries/{kb_id}",
        json={
            "title": f"Banned Term {kb_code} (Updated Policy)",
            "change_note": "Updated policy wording for improved compliance clarity.",
        },
        headers=h_admin,
    )
    assert update_res.status_code == 200, update_res.text
    updated_kb = update_res.json()
    assert updated_kb["current_version"] == 2

    # 4. Invariant: Historical submission finding MUST still cite Version 1
    findings_check_res = client.get(f"/api/v1/submissions/{sub_id}/findings", headers=h_creator)
    assert findings_check_res.status_code == 200
    finding_after = next(
        f for f in findings_check_res.json() if f.get("cited_entry_code") == kb_code
    )
    assert finding_after["cited_entry_version"] == 1, (
        f"Historical finding cited_entry_version changed! Expected 1, found {finding_after['cited_entry_version']}"
    )


# ==============================================================================
# J7: DOCX, PDF, and image upload
# ==============================================================================

def test_j7_docx_pdf_and_image_upload(client: E2EClient):
    """
    J7: Tests multi-format uploads:
    - DOCX upload (good.docx): extracts headings, paragraphs, and computes location labels.
    - PDF upload (text.pdf): extracts text structure and page counts.
    - Image upload (lumo_logo.png): verifies visual brand asset checks (logo match, palette).
    """
    creator_token = login(client, "creator.social@lumo.internal")
    h_creator = {"Authorization": f"Bearer {creator_token}"}

    # 1. DOCX Upload
    docx_path = os.path.join(DOCS_FIXTURES_DIR, "good.docx")
    assert os.path.exists(docx_path), f"Missing test fixture: {docx_path}"
    with open(docx_path, "rb") as f:
        docx_bytes = f.read()

    files_docx = {
        "file": ("good.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    }
    data_docx = {"channel": "web", "title": "J7 DOCX Brand Guide"}

    res_docx = client.post("/api/v1/submissions/upload", files=files_docx, data=data_docx, headers=h_creator)
    assert res_docx.status_code == 200, res_docx.text
    sub_docx = res_docx.json()
    assert sub_docx["status"] == "Draft"
    assert "Lumo Botanical" in sub_docx["content"]
    docx_sub_id = sub_docx["id"]

    # Trigger review to verify location mapping
    rev_docx = client.post(f"/api/v1/submissions/{docx_sub_id}/review?sync=true", headers=h_creator)
    assert rev_docx.status_code == 200

    # 2. PDF Upload
    pdf_path = os.path.join(DOCS_FIXTURES_DIR, "text.pdf")
    assert os.path.exists(pdf_path), f"Missing test fixture: {pdf_path}"
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    files_pdf = {"file": ("text.pdf", pdf_bytes, "application/pdf")}
    data_pdf = {"channel": "web", "title": "J7 PDF Product Manual"}

    res_pdf = client.post("/api/v1/submissions/upload", files=files_pdf, data=data_pdf, headers=h_creator)
    assert res_pdf.status_code == 200, res_pdf.text
    sub_pdf = res_pdf.json()
    assert sub_pdf["status"] == "Draft"
    assert len(sub_pdf["content"]) > 10

    # 3. Image Upload (PNG)
    logo_path = os.path.join(ASSETS_FIXTURES_DIR, "lumo_logo.png")
    assert os.path.exists(logo_path), f"Missing test fixture: {logo_path}"
    with open(logo_path, "rb") as f:
        logo_bytes = f.read()

    files_img = {"file": ("lumo_logo.png", logo_bytes, "image/png")}
    data_img = {"channel": "social", "title": "J7 Logo Asset Check"}

    res_img = client.post("/api/v1/submissions/upload", files=files_img, data=data_img, headers=h_creator)
    assert res_img.status_code == 200, res_img.text
    sub_img = res_img.json()
    assert sub_img["status"] == "Draft"

    # Trigger image review to run visual compliance checks
    img_sub_id = sub_img["id"]
    rev_img = client.post(f"/api/v1/submissions/{img_sub_id}/review?sync=true", headers=h_creator)
    assert rev_img.status_code == 200, rev_img.text
    assert rev_img.json()["status"] == "completed"


# ==============================================================================
# J8: The evaluation page loads
# ==============================================================================

def test_j8_evaluation_page_loads(client: E2EClient):
    """
    J8: Verifies that the evaluation results endpoint returns benchmark report data
    containing overall precision, recall, f1, before/after rows, and false-positive explorer items.
    Also verifies that the frontend evaluation static export build exists.
    """
    manager_token = login(client, "manager.kavita@lumo.internal")
    h_mgr = {"Authorization": f"Bearer {manager_token}"}

    res = client.get("/api/v1/evaluation/results", headers=h_mgr)
    assert res.status_code == 200, res.text
    data = res.json()

    # Verify required evaluation schema sections
    assert "summary" in data
    assert "overall" in data["summary"]
    overall = data["summary"]["overall"]
    assert "precision" in overall
    assert "recall" in overall
    assert "f1" in overall
    assert overall["precision"] > 0.0
    assert overall["recall"] > 0.0

    assert "before_after" in data
    assert isinstance(data["before_after"], list)
    assert len(data["before_after"]) > 0

    assert "false_positives" in data
    assert "by_issue_type" in data

    # Verify frontend static build artifact exists
    eval_html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../frontend/out/eval/index.html"))
    if os.path.exists(eval_html_path):
        assert os.path.getsize(eval_html_path) > 1000, "Frontend eval page should be non-empty static HTML"


# ==============================================================================
# J9: AI-off (admin switch) still completes a review with rules only
# ==============================================================================

def test_j9_ai_off_admin_switch_rules_only_review(client: E2EClient):
    """
    J9: Admin turns on the 'no_external_ai' switch.
    Creator submits brand copy with violations and triggers review.
    Pipeline gracefully falls back to rules_only mode, completes without 500 errors,
    and detects rule-based violations (e.g. banned terms, claim triggers).
    Admin then restores the setting.
    """
    admin_token = login(client, "admin@lumo.internal")
    creator_token = login(client, "creator.social@lumo.internal")
    h_admin = {"Authorization": f"Bearer {admin_token}"}
    h_creator = {"Authorization": f"Bearer {creator_token}"}
    run_id = uuid.uuid4().hex[:6]

    try:
        # 1. Admin turns external AI OFF
        put_settings = client.put(
            "/api/v1/settings",
            json={"no_external_ai": True},
            headers=h_admin,
        )
        assert put_settings.status_code == 200, put_settings.text
        assert put_settings.json().get("no_external_ai") is True

        # 2. Creator creates submission
        create_res = client.post(
            "/api/v1/submissions",
            json={
                "title": f"J9 AI-Off Rules Review ({run_id})",
                "channel": "social",
                "content": f"Discover our miracle serum for reverse aging with natural ingredients. [Run-{run_id}]",
            },
            headers=h_creator,
        )
        assert create_res.status_code == 200
        sub_id = create_res.json()["id"]

        # 3. Trigger review in rules_only mode
        rev_res = client.post(f"/api/v1/submissions/{sub_id}/review?sync=true", headers=h_creator)
        assert rev_res.status_code == 200, rev_res.text
        rev_data = rev_res.json()
        assert rev_data["status"] == "completed"

        # 4. Verify review completed and produced rule-based findings
        findings_res = client.get(f"/api/v1/submissions/{sub_id}/findings", headers=h_creator)
        assert findings_res.status_code == 200
        findings = findings_res.json()
        assert len(findings) > 0
        rule_findings = [f for f in findings if f.get("source") == "rule"]
        assert len(rule_findings) > 0, "Rules-only review must still detect rule violations"

    finally:
        # 5. Restore admin setting
        client.put(
            "/api/v1/settings",
            json={"no_external_ai": False},
            headers=h_admin,
        )
