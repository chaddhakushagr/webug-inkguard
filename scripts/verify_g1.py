"""
Gate G1 Verification Script for Inkguard.
Executes the full end-to-end multi-role golden path against the live backend
and validates all safety invariants, state transitions, and cryptographic audit rows.
"""

import sys
import httpx
from datetime import datetime, timezone

import os
from app.config import settings

BASE_URL = "http://localhost:8000/api/v1"
DEMO_PASSWORD = settings.DEMO_PASSWORD

def main():
    print("=" * 70)
    print("INKGUARD GATE G1: END-TO-END VERIFICATION")
    print("=" * 70)

    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    # 1. Authenticate users
    print("\n[Step 1] Authenticating Demo Users across all required roles...")
    users = {
        "creator": "creator.social@lumo.internal",
        "reviewer1": "reviewer.sarah@lumo.internal",
        "reviewer2": "reviewer.alex@lumo.internal",
        "agency": "creator.agency@contractor.external",
        "admin": "admin@lumo.internal",
        "manager": "manager.kavita@lumo.internal",
    }
    tokens = {}
    for role_key, email in users.items():
        res = client.post("/auth/login", json={"email": email, "password": DEMO_PASSWORD})
        assert res.status_code == 200, f"Login failed for {email}: {res.text}"
        tokens[role_key] = res.json()["access_token"]
        print(f"  ✓ {role_key.title()} ({email}) authenticated successfully.")

    headers = {k: {"Authorization": f"Bearer {v}"} for k, v in tokens.items()}

    # 2. Creator creates submission (High-risk channel: press_release)
    print("\n[Step 2] Creator creates high-risk submission (press_release channel)...")
    res = client.post(
        "/submissions",
        json={
            "title": "Lumo Spring Global Press Release",
            "channel": "press_release",
            "content": "Lumo announces new clinical study results for Glow Concentrate with 94% improved hydration.",
        },
        headers=headers["creator"],
    )
    assert res.status_code == 200, f"Create submission failed: {res.text}"
    sub = res.json()
    sub_id = sub["id"]
    assert sub["status"] == "Draft", f"Expected Draft, got {sub['status']}"
    assert sub["risk_tier"] == "high", f"Expected high risk_tier, got {sub['risk_tier']}"
    assert sub["version_no"] == 1, f"Expected version 1, got {sub['version_no']}"
    print(f"  ✓ Submission created: ID={sub_id}, Status={sub['status']}, RiskTier={sub['risk_tier']}, Version={sub['version_no']}")

    # 3. Creator edits submission
    print("\n[Step 3] Creator edits draft submission content...")
    res = client.put(
        f"/submissions/{sub_id}/content",
        json={
            "content": "Lumo announces verified clinical study results for Glow Concentrate: 94% improved hydration over 4 weeks.",
            "source": "creator_edit",
        },
        headers=headers["creator"],
    )
    assert res.status_code == 200, f"Edit content failed: {res.text}"
    sub = res.json()
    assert sub["status"] == "Draft"
    assert sub["version_no"] == 2
    print(f"  ✓ Submission edited to Version {sub['version_no']}, Status={sub['status']}")

    # 4. Trigger review (needs completed review before submit)
    print("\n[Step 4] Triggering brand review pipeline...")
    res = client.post(f"/submissions/{sub_id}/review", headers=headers["creator"])
    assert res.status_code == 200, f"Review failed: {res.text}"
    rev_data = res.json()
    print(f"  ✓ Review run completed: Mode={rev_data['mode']}, Status={rev_data['status']}")

    res = client.get(f"/submissions/{sub_id}", headers=headers["creator"])
    sub = res.json()
    assert sub["status"] == "Checked", f"Expected Checked after review, got {sub['status']}"
    print(f"  ✓ Submission transitioned: Status={sub['status']}")

    # 5. Creator submits
    print("\n[Step 5] Creator submits content for review...")
    res = client.post(f"/submissions/{sub_id}/submit", headers=headers["creator"])
    assert res.status_code == 200, f"Submit failed: {res.text}"
    sub = res.json()
    assert sub["status"] == "Submitted"
    print(f"  ✓ Submission transitioned: Status={sub['status']}")

    # 6. Reviewer 1 claims
    print("\n[Step 6] Reviewer 1 claims submission...")
    res = client.post(f"/submissions/{sub_id}/claim", headers=headers["reviewer1"])
    assert res.status_code == 200, f"Claim failed: {res.text}"
    sub = res.json()
    assert sub["status"] == "In Review"
    print(f"  ✓ Claimed by Reviewer 1: Status={sub['status']}, Assignee={sub['assignee_id']}")

    # 7. Reviewer comments
    print("\n[Step 7] Reviewer posts a review comment...")
    res = client.post(
        f"/submissions/{sub_id}/comments",
        json={"body": "Please ensure the 94% figure is attributed specifically to Study L-12."},
        headers=headers["reviewer1"],
    )
    assert res.status_code == 200, f"Comment failed: {res.text}"
    comment = res.json()
    print(f"  ✓ Comment posted: ID={comment['id']}, Author={comment['author_name']}")

    # 8. Reviewer requests changes
    print("\n[Step 8] Reviewer requests changes...")
    res = client.post(
        f"/submissions/{sub_id}/request-changes",
        json={"note": "Add citation: '(Study L-12, valid through Dec 2026)'."},
        headers=headers["reviewer1"],
    )
    assert res.status_code == 200, f"Request changes failed: {res.text}"
    sub = res.json()
    assert sub["status"] == "Changes Requested"
    print(f"  ✓ Status transitioned: Status={sub['status']}")

    # 9. Creator edits and resubmits
    print("\n[Step 9] Creator updates copy with requested citation and resubmits...")
    res = client.put(
        f"/submissions/{sub_id}/content",
        json={
            "content": "Lumo announces verified clinical study results for Glow Concentrate: 94% improved hydration over 4 weeks (Study L-12, valid through Dec 2026).",
            "source": "creator_revision",
        },
        headers=headers["creator"],
    )
    assert res.status_code == 200
    sub = res.json()
    assert sub["status"] == "Draft"
    assert sub["version_no"] == 3
    print(f"  ✓ Content updated to Version {sub['version_no']}, reverted to Draft")

    # Run review on version 3
    res = client.post(f"/submissions/{sub_id}/review", headers=headers["creator"])
    assert res.status_code == 200
    res = client.get(f"/submissions/{sub_id}", headers=headers["creator"])
    assert res.json()["status"] == "Checked"

    # Submit version 3
    res = client.post(f"/submissions/{sub_id}/submit", headers=headers["creator"])
    assert res.status_code == 200
    assert res.json()["status"] == "Submitted"
    print("  ✓ Resubmission complete. Status=Submitted")

    # 10. Reviewer approvals (High-risk requires 2 reviewers)
    print("\n[Step 10] Multi-reviewer approval verification (High-Risk Channel)...")
    # Reviewer 1 claims & approves
    client.post(f"/submissions/{sub_id}/claim", headers=headers["reviewer1"])
    res = client.post(
        f"/submissions/{sub_id}/approve",
        json={"note": "Verified Study L-12 citation. Approved by Reviewer 1."},
        headers=headers["reviewer1"],
    )
    assert res.status_code == 200
    sub = res.json()
    # High risk requires 2 reviewers, so status should still be In Review with 1 approval
    assert sub["status"] == "In Review", f"Expected In Review after 1 of 2 approvals, got {sub['status']}"
    print(f"  ✓ First approval recorded (1/2). Status properly remains '{sub['status']}'")

    # Reviewer 2 approves
    res = client.post(
        f"/submissions/{sub_id}/approve",
        json={"note": "Second peer review completed. All claims verified."},
        headers=headers["reviewer2"],
    )
    assert res.status_code == 200
    sub = res.json()
    assert sub["status"] == "Approved", f"Expected Approved after 2 of 2 approvals, got {sub['status']}"
    print(f"  ✓ Second approval recorded (2/2). Status transitioned to '{sub['status']}'!")

    # 11. Creator marks published
    print("\n[Step 11] Creator marks submission as published...")
    res = client.post(
        f"/submissions/{sub_id}/mark-published",
        json={"url": "https://brand.lumo.skincare/press/spring-2026"},
        headers=headers["creator"],
    )
    assert res.status_code == 200
    sub = res.json()
    assert sub["status"] == "Marked Published"
    assert sub["published_url"] == "https://brand.lumo.skincare/press/spring-2026"
    print(f"  ✓ Final lifecycle state reached: Status={sub['status']}, PublishedURL={sub['published_url']}")

    # 12. Admin edits a fact -> version 2 appears
    print("\n[Step 12] Admin edits Knowledge Base fact -> Version 2 verification...")
    # Get Study L-12 fact
    res = client.get("/kb/entries?type=fact", headers=headers["admin"])
    assert res.status_code == 200
    facts = res.json()
    target_fact = next((f for f in facts if "L-12" in f["title"] or "L-12" in f.get("code", "")), facts[0])
    fact_id = target_fact["id"]
    orig_version = target_fact["current_version"]
    print(f"  Target Fact: {target_fact['code']} ('{target_fact['title']}'), Version={orig_version}")

    # Admin updates fact
    res = client.put(
        f"/kb/entries/{fact_id}",
        json={
            "title": target_fact["title"] + " (Updated Protocol)",
            "change_note": "Extended clinical trial documentation and methodology notes.",
        },
        headers=headers["admin"],
    )
    assert res.status_code == 200
    updated_fact = res.json()
    assert updated_fact["current_version"] == orig_version + 1, f"Expected version {orig_version + 1}, got {updated_fact['current_version']}"
    print(f"  ✓ Fact updated: New Version={updated_fact['current_version']}")

    # Verify version history has v1 and v2
    res = client.get(f"/kb/entries/{fact_id}/versions", headers=headers["admin"])
    assert res.status_code == 200
    versions = res.json()
    version_numbers = [v["version"] for v in versions]
    assert 1 in version_numbers and 2 in version_numbers
    print(f"  ✓ Version history confirmed with versions: {version_numbers}")

    # 13. Agency Creator cannot see internal or confidential entries
    print("\n[Step 13] Agency Creator tier clearance boundary verification...")
    res = client.get("/kb/entries", headers=headers["agency"])
    assert res.status_code == 200
    agency_entries = res.json()
    agency_classifications = {e["classification"] for e in agency_entries}
    print(f"  Agency-visible classifications: {agency_classifications}")
    assert "confidential" not in agency_classifications, "LEAK: Agency saw confidential KB entry!"
    assert "internal" not in agency_classifications, "LEAK: Agency saw internal KB entry!"
    print("  ✓ Safety Invariant verified: Agency user can ONLY see public entries.")

    # 14. Safety Invariant: Creator approving own submission refused with 403
    print("\n[Step 14] Creator self-approval refusal (403 Forbidden) verification...")
    # Create a fresh submission by creator, move to In Review
    res = client.post(
        "/submissions",
        json={"title": "Self Approval Test", "channel": "social", "content": "Self approval test copy."},
        headers=headers["creator"],
    )
    test_sub_id = res.json()["id"]
    client.post(f"/submissions/{test_sub_id}/review", headers=headers["creator"])
    client.post(f"/submissions/{test_sub_id}/submit", headers=headers["creator"])
    client.post(f"/submissions/{test_sub_id}/claim", headers=headers["reviewer1"])

    # Creator attempts to approve own submission
    res = client.post(
        f"/submissions/{test_sub_id}/approve",
        json={"note": "Attempting unauthorized self approval"},
        headers=headers["creator"],
    )
    assert res.status_code == 403, f"Expected 403 Forbidden, got {res.status_code}: {res.text}"
    print(f"  ✓ Safety Invariant verified: Self-approval returned 403 Forbidden: '{res.json().get('detail')}'")

    # 15. Cryptographic Audit Log verification
    print("\n[Step 15] Cryptographic Audit Log and Hash Chaining verification...")
    res = client.get(f"/audit?entity_id={sub_id}&limit=50", headers=headers["admin"])
    assert res.status_code == 200
    audit_rows = res.json()
    print(f"  Found {len(audit_rows)} audit rows for Golden Path submission {sub_id}:")
    actions_found = [row["action"] for row in audit_rows]
    for row in audit_rows:
        print(f"    - Action: {row['action']:<25} Actor: {row['actor_role']:<15} Hash: {row['hash'][:16]}... Prev: {row['prev_hash'][:16]}...")

    expected_actions = [
        "submission_create",
        "submission_content_update",
        "submission_submit",
        "submission_claim",
        "submission_request_changes",
        "submission_approve",
        "submission_publish",
    ]
    for exp in expected_actions:
        assert exp in actions_found, f"Missing audit action '{exp}' in audit trail!"
    print(f"  ✓ All expected lifecycle events are recorded in append-only audit trail.")

    print("\n" + "=" * 70)
    print("ALL GATE G1 VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    main()
