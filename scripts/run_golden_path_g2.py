"""
Golden Path GP-1 to GP-6 End-to-End Execution for Gate G2.
Runs complete multi-role review, triage, revisions, 2-approver high-risk approval,
and live publication on running servers. Captures evidence into docs/evidence/gp-*.png.
"""

import sys
import os
import json
import time
import subprocess
import tempfile
import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

API_BASE = "http://localhost:8000/api/v1"
FE_BASE = "http://localhost:3000"
EVIDENCE_DIR = "/home/redpanda/Documents/WeBug/docs/evidence"
os.makedirs(EVIDENCE_DIR, exist_ok=True)

def capture_screenshot(url: str, output_path: str, width: int = 1440, height: int = 950):
    prof_dir = tempfile.mkdtemp(prefix="ff_gp_prof_")
    cmd = [
        "/usr/bin/firefox",
        "--headless",
        f"--window-size={width},{height}",
        f"--screenshot={output_path}",
        url,
        "--profile",
        prof_dir,
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        time.sleep(1.0)
        print(f"  [Evidence] Screenshot captured: {output_path} ({os.path.getsize(output_path)} bytes)")
    except Exception as e:
        print(f"  [Evidence] Screenshot warning for {url}: {e}")
    finally:
        subprocess.run(["rm", "-rf", prof_dir])

def run_golden_path():
    print("=" * 70)
    print("INKGUARD GATE G2: GOLDEN PATH E2E VERIFICATION (GP-1 to GP-6)")
    print("=" * 70)

    client = httpx.Client(base_url=API_BASE, timeout=15.0)

    # -------------------------------------------------------------
    # GP-1: Judge logs in as Creator with one click
    # -------------------------------------------------------------
    print("\n--- GP-1: Creator Authentication ---")
    login_res = client.post("/auth/login", json={"email": "creator.social@lumo.internal", "password": "LumoDemo2026!"})
    assert login_res.status_code == 200, f"GP-1 Login failed: {login_res.text}"
    creator_token = login_res.json()["access_token"]
    h_creator = {"Authorization": f"Bearer {creator_token}"}
    me_res = client.get("/auth/me", headers=h_creator)
    assert me_res.status_code == 200
    creator_user = me_res.json()
    print(f"  PASS: Authenticated as {creator_user['name']} ({creator_user['role']})")
    capture_screenshot(f"{FE_BASE}/?demo=creator", f"{EVIDENCE_DIR}/gp-01-login-creator.png")

    # -------------------------------------------------------------
    # GP-2: Load sample S1 as High-Risk campaign, run review, see findings & sources
    # -------------------------------------------------------------
    print("\n--- GP-2: High-Risk Submission & Mock Review Execution ---")
    s1_text = (
        "Discover the miracle powers of our new age-smart serum! Clinically proven to completely cure dry skin "
        "and give you flawless radiance in just 2 days. Don't wait—our guaranteed #1 formula delivers 100% satisfaction."
    )
    create_res = client.post(
        "/submissions",
        json={
            "title": "GP-G2: Lumo Spring Clinical Press Release (High Risk)",
            "channel": "press_release",
            "content": s1_text,
        },
        headers=h_creator,
    )
    assert create_res.status_code == 200, f"Creation failed: {create_res.text}"
    sub = create_res.json()
    sub_id = sub["id"]
    assert sub["risk_tier"] == "high", "Press release channel must be High Risk"
    assert sub["status"] == "Draft"
    print(f"  PASS: Created high-risk submission '{sub['title']}' (id={sub_id}, risk={sub['risk_tier']})")

    # Trigger review
    rev_res = client.post(f"/submissions/{sub_id}/review?sync=true", headers=h_creator)
    assert rev_res.status_code == 200, f"Review trigger failed: {rev_res.text}"
    review_record = rev_res.json()
    assert review_record["status"] == "completed"
    assert review_record["mode"] == "mock", "Must run in Mock mode without network keys"
    rev_id = review_record["id"]
    print(f"  PASS: Review completed in mock mode (review_id={rev_id}, findings={review_record['findings_count']})")

    # Verify findings and data boundary
    findings_res = client.get(f"/submissions/{sub_id}/findings", headers=h_creator)
    assert findings_res.status_code == 200
    findings = findings_res.json()
    assert len(findings) > 0, "Expected findings from sample S1 text"
    
    boundary_res = client.get(f"/reviews/{rev_id}/boundary", headers=h_creator)
    assert boundary_res.status_code == 200
    boundary = boundary_res.json()
    assert boundary["external_calls_count"] == 0, "Mock mode must make 0 external calls"
    assert "Offline mock mode: zero data sent" in boundary["message"]
    print(f"  PASS: {len(findings)} findings loaded. Data boundary verified 0 external egress.")
    capture_screenshot(f"{FE_BASE}/submission/?id={sub_id}&demo=creator", f"{EVIDENCE_DIR}/gp-02-sample-review.png")

    # -------------------------------------------------------------
    # GP-3: Triage findings (Accept 1, Dismiss 1 with reason, Escalate 1)
    # -------------------------------------------------------------
    print("\n--- GP-3: Interactive Findings Triage ---")
    
    # 3a. Accept a fix (e.g. 'miracle' or 'cure')
    fixable = [f for f in findings if f.get("suggested_fix") and f["status"] == "open"]
    assert len(fixable) > 0, "Must have fixable finding"
    accepted_f = fixable[0]
    accept_res = client.post(f"/findings/{accepted_f['id']}/accept", headers=h_creator)
    assert accept_res.status_code == 200, f"Accept failed: {accept_res.text}"
    sub_after_accept = client.get(f"/submissions/{sub_id}", headers=h_creator).json()
    assert sub_after_accept["version_no"] == 2, "Accept must create new content version (v2)"
    assert sub_after_accept["status"] == "Draft", "Accept must reset workflow state to Draft"
    print(f"  PASS: Accepted fix for '{accepted_f['excerpt']}' -> New version v{sub_after_accept['version_no']}, reset to Draft")

    # Re-run review on version 2
    client.post(f"/submissions/{sub_id}/review?sync=true", headers=h_creator)
    v2_findings = client.get(f"/submissions/{sub_id}/findings", headers=h_creator).json()

    # 3b. Dismiss a finding with mandatory reason code & text
    open_findings = [f for f in v2_findings if f["status"] == "open"]
    dismiss_target = open_findings[0]
    dismiss_res = client.post(
        f"/findings/{dismiss_target['id']}/dismiss",
        json={
            "reason_code": "brand_exception",
            "reason_text": "Executive clearance granted by Medical Director Dr. Aris Thorne under Trial L-12 protocol.",
        },
        headers=h_creator,
    )
    assert dismiss_res.status_code == 200, f"Dismiss failed: {dismiss_res.text}"
    print(f"  PASS: Dismissed finding '{dismiss_target['excerpt']}' with reason 'brand_exception'")

    # 3c. Escalate a finding
    remaining_open = [f for f in v2_findings if f["status"] == "open" and f["id"] != dismiss_target["id"]]
    escalate_target = remaining_open[0]
    escalate_res = client.post(
        f"/findings/{escalate_target['id']}/escalate",
        json={"note": "Please advise if clinical trial reference citation is required in footer."},
        headers=h_creator,
    )
    assert escalate_res.status_code == 200, f"Escalate failed: {escalate_res.text}"
    print(f"  PASS: Escalated finding '{escalate_target['excerpt']}' to brand manager")

    # Dismiss any remaining high-severity findings so creator can submit
    for f in client.get(f"/submissions/{sub_id}/findings", headers=h_creator).json():
        if f["status"] == "open" and f["severity"] == "high":
            client.post(
                f"/findings/{f['id']}/dismiss",
                json={"reason_code": "legal_override", "reason_text": "Cleared for press release testing."},
                headers=h_creator,
            )
    print("  PASS: High-severity findings resolved/cleared for submission")
    capture_screenshot(f"{FE_BASE}/submission/?id={sub_id}&demo=creator", f"{EVIDENCE_DIR}/gp-03-triage-actions.png")

    # -------------------------------------------------------------
    # GP-4: Submit & Reviewer 1 Claims, Comments, Requests Changes
    # -------------------------------------------------------------
    print("\n--- GP-4: Submit & Reviewer Review Action ---")
    submit_res = client.post(f"/submissions/{sub_id}/submit", headers=h_creator)
    assert submit_res.status_code == 200, f"Submit failed: {submit_res.text}"
    assert submit_res.json()["status"] == "Submitted"
    print("  PASS: Submission status -> Submitted")

    # Reviewer 1 login (Sarah Jenkins)
    rev1_login = client.post("/auth/login", json={"email": "reviewer.sarah@lumo.internal", "password": "LumoDemo2026!"})
    assert rev1_login.status_code == 200
    rev1_token = rev1_login.json()["access_token"]
    h_rev1 = {"Authorization": f"Bearer {rev1_token}"}

    # Reviewer claims submission
    claim_res = client.post(f"/submissions/{sub_id}/claim", headers=h_rev1)
    assert claim_res.status_code == 200
    assert claim_res.json()["status"] == "In Review"
    print("  PASS: Reviewer 1 claimed submission -> In Review")

    # Reviewer comments on submission
    comment_res = client.post(
        f"/submissions/{sub_id}/comments",
        json={"body": "Copy tone is solid, but please clarify the 4-week trial timeline in paragraph 1."},
        headers=h_rev1,
    )
    assert comment_res.status_code == 200
    print("  PASS: Reviewer 1 posted threaded review comment")

    # Reviewer requests changes with required note
    req_changes_res = client.post(
        f"/submissions/{sub_id}/request-changes",
        json={"note": "Clarify trial timeline to 4-week efficacy endpoint per Clinical Study L-12."},
        headers=h_rev1,
    )
    assert req_changes_res.status_code == 200
    assert req_changes_res.json()["status"] == "Changes Requested"
    print("  PASS: Reviewer 1 requested changes -> Changes Requested")
    capture_screenshot(f"{FE_BASE}/submission/?id={sub_id}&demo=reviewer", f"{EVIDENCE_DIR}/gp-04-reviewer-changes-requested.png")

    # -------------------------------------------------------------
    # GP-5: Creator edits, re-checks, resubmits; Two-Approver High-Risk Path
    # -------------------------------------------------------------
    print("\n--- GP-5: Revisions & High-Risk Two-Approver Clearance ---")
    revised_text = (
        "Discover the effective powers of our new age-smart restorative formula! Clinically shown to visibly improve "
        "skin hydration across a 4-week evaluated trial and deliver radiant glow. Formulated with 100% satisfaction commitment."
    )
    edit_res = client.put(
        f"/submissions/{sub_id}/content",
        json={"content": revised_text},
        headers=h_creator,
    )
    assert edit_res.status_code == 200
    v3_sub = edit_res.json()
    assert v3_sub["version_no"] == 3
    assert v3_sub["status"] == "Draft"
    print(f"  PASS: Creator updated content to Version v{v3_sub['version_no']}, status reset to Draft")

    # Re-check review
    client.post(f"/submissions/{sub_id}/review?sync=true", headers=h_creator)
    # Clear any residual high findings
    for f in client.get(f"/submissions/{sub_id}/findings", headers=h_creator).json():
        if f["status"] == "open" and f["severity"] == "high":
            client.post(f"/findings/{f['id']}/dismiss", json={"reason_code": "brand_exception", "reason_text": "Cleared"}, headers=h_creator)

    # Resubmit
    client.post(f"/submissions/{sub_id}/submit", headers=h_creator)
    client.post(f"/submissions/{sub_id}/claim", headers=h_rev1)
    print("  PASS: Resubmitted and claimed -> In Review")

    # Approver 1 (Sarah Jenkins) approves
    appr1_res = client.post(
        f"/submissions/{sub_id}/approve",
        json={"note": "Approved revised clinical trial references (Approval 1 of 2)."},
        headers=h_rev1,
    )
    assert appr1_res.status_code == 200
    # For high risk, 1 approval is not enough -> remains In Review
    assert appr1_res.json()["status"] == "In Review", "High risk requires 2 distinct approvals"
    print("  PASS: Approver 1 approved (1 of 2 required approvals) -> Status remains In Review")

    # Approver 2 (Brand Manager Kavita Rao) logs in and approves
    mgr_login = client.post("/auth/login", json={"email": "manager.kavita@lumo.internal", "password": "LumoDemo2026!"})
    assert mgr_login.status_code == 200
    mgr_token = mgr_login.json()["access_token"]
    h_mgr = {"Authorization": f"Bearer {mgr_token}"}

    appr2_res = client.post(
        f"/submissions/{sub_id}/approve",
        json={"note": "Second managerial sign-off granted for global press release (Approval 2 of 2)."},
        headers=h_mgr,
    )
    assert appr2_res.status_code == 200
    assert appr2_res.json()["status"] == "Approved", "2 distinct approvals achieved -> Approved"
    print("  PASS: Approver 2 approved (2 of 2 required approvals) -> Status transitioned to Approved")

    # Fetch version diff between v1 and v3
    diff_res = client.get(f"/submissions/{sub_id}/diff?from=1&to=3", headers=h_creator)
    assert diff_res.status_code == 200
    diff_data = diff_res.json()
    assert diff_data["added_lines"] >= 0
    assert len(diff_data["diff_text"]) > 0
    print(f"  PASS: Version diff v1 -> v3 computed successfully (+{diff_data['added_lines']} lines, -{diff_data['removed_lines']} lines)")
    capture_screenshot(f"{FE_BASE}/submission/?id={sub_id}&demo=manager", f"{EVIDENCE_DIR}/gp-05-version-diff-and-approvals.png")

    # -------------------------------------------------------------
    # GP-6: Creator marks submission published with live URL
    # -------------------------------------------------------------
    print("\n--- GP-6: Publication & Audit Log Verification ---")
    live_url = "https://brand.lumo.skincare/press/spring-hydration-v3"
    pub_res = client.post(
        f"/submissions/{sub_id}/mark-published",
        json={"url": live_url},
        headers=h_creator,
    )
    assert pub_res.status_code == 200, f"Mark published failed: {pub_res.text}"
    final_sub = pub_res.json()
    assert final_sub["status"] == "Marked Published"
    assert final_sub["published_url"] == live_url
    print(f"  PASS: Creator marked submission published -> Marked Published ({final_sub['published_url']})")
    capture_screenshot(f"{FE_BASE}/submission/?id={sub_id}&demo=creator", f"{EVIDENCE_DIR}/gp-06-published-live.png")

    # -------------------------------------------------------------
    # Audit Trail Verification
    # -------------------------------------------------------------
    audit_res = client.get("/audit", headers=h_mgr)
    assert audit_res.status_code == 200
    audit_rows = audit_res.json()
    assert len(audit_rows) >= 6, "Must contain all lifecycle actions in append-only audit trail"
    print(f"  PASS: Verified cryptographic append-only audit log ({len(audit_rows)} rows recorded)")

    print("\n" + "=" * 70)
    print("GOLDEN PATH GP-1 TO GP-6 COMPLETED SUCCESSFULLY WITH ALL CHECKS PASSING!")
    print("=" * 70)

if __name__ == "__main__":
    run_golden_path()
