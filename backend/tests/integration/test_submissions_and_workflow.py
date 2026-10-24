from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def get_token(email: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": settings.DEMO_PASSWORD})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_full_workflow_lifecycle():
    creator_token = get_token("creator.social@lumo.internal")
    reviewer1_token = get_token("reviewer.sarah@lumo.internal")
    reviewer2_token = get_token("reviewer.alex@lumo.internal")
    manager_token = get_token("manager.kavita@lumo.internal")

    h_creator = {"Authorization": f"Bearer {creator_token}"}
    h_rev1 = {"Authorization": f"Bearer {reviewer1_token}"}
    h_rev2 = {"Authorization": f"Bearer {reviewer2_token}"}
    h_mgr = {"Authorization": f"Bearer {manager_token}"}

    # Step 1: Creator creates submission
    create_res = client.post(
        "/api/v1/submissions",
        json={
            "title": "Summer Campaign Post",
            "channel": "social",
            "content": "Experience our new hydrating miracle serum with cold-pressed rosehip seed extract.",
        },
        headers=h_creator,
    )
    assert create_res.status_code == 200
    sub = create_res.json()
    assert sub["status"] == "Draft"
    assert sub["risk_tier"] == "low"
    sub_id = sub["id"]

    # Step 2: Trigger review -> moves to Checked
    rev_res = client.post(f"/api/v1/submissions/{sub_id}/review", headers=h_creator)
    assert rev_res.status_code == 200

    sub_res = client.get(f"/api/v1/submissions/{sub_id}", headers=h_creator)
    assert sub_res.json()["status"] == "Checked"

    # Step 3: Creator submits -> moves to Submitted
    submit_res = client.post(f"/api/v1/submissions/{sub_id}/submit", headers=h_creator)
    assert submit_res.status_code == 200
    assert submit_res.json()["status"] == "Submitted"

    # Step 4: Reviewer claims -> moves to In Review
    claim_res = client.post(f"/api/v1/submissions/{sub_id}/claim", headers=h_rev1)
    assert claim_res.status_code == 200
    assert claim_res.json()["status"] == "In Review"

    # Step 5: Post a comment
    comment_res = client.post(
        f"/api/v1/submissions/{sub_id}/comments",
        json={"body": "Please remove 'miracle serum' phrasing."},
        headers=h_rev1,
    )
    assert comment_res.status_code == 200
    assert comment_res.json()["body"] == "Please remove 'miracle serum' phrasing."

    # Step 6: Reviewer requests changes (requires note)
    req_changes_res = client.post(
        f"/api/v1/submissions/{sub_id}/request-changes",
        json={"note": "Please update product designation to Lumo Glow Concentrate."},
        headers=h_rev1,
    )
    assert req_changes_res.status_code == 200
    assert req_changes_res.json()["status"] == "Changes Requested"

    # Step 7: Creator edits content -> creates version 2 and returns to Draft
    edit_res = client.put(
        f"/api/v1/submissions/{sub_id}/content",
        json={"content": "Experience our new hydrating Lumo Glow Concentrate with cold-pressed rosehip seed extract."},
        headers=h_creator,
    )
    assert edit_res.status_code == 200
    sub_edited = edit_res.json()
    assert sub_edited["status"] == "Draft"
    assert sub_edited["version_no"] == 2

    # Step 8: Verify diff endpoint
    diff_res = client.get(f"/api/v1/submissions/{sub_id}/diff?from=1&to=2", headers=h_creator)
    assert diff_res.status_code == 200
    diff_data = diff_res.json()
    assert diff_data["from_version"] == 1
    assert diff_data["to_version"] == 2
    assert "miracle serum" in diff_data["diff_text"]
    assert "Lumo Glow Concentrate" in diff_data["diff_text"]

    # Step 9: Creator submits revised version -> Checked then Submitted
    client.post(f"/api/v1/submissions/{sub_id}/review", headers=h_creator)
    client.post(f"/api/v1/submissions/{sub_id}/submit", headers=h_creator)

    # Step 10: Reviewer claims and approves
    client.post(f"/api/v1/submissions/{sub_id}/claim", headers=h_rev1)

    # Invariant: Creator CANNOT approve own submission (403 Forbidden)
    self_approve_res = client.post(f"/api/v1/submissions/{sub_id}/approve", headers=h_creator)
    assert self_approve_res.status_code == 403

    # Reviewer approves
    approve_res = client.post(f"/api/v1/submissions/{sub_id}/approve", headers=h_rev1)
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "Approved"

    # Step 11: Mark published
    pub_res = client.post(
        f"/api/v1/submissions/{sub_id}/mark-published",
        json={"url": "https://instagram.com/p/lumo-summer-launch"},
        headers=h_creator,
    )
    assert pub_res.status_code == 200
    pub_data = pub_res.json()
    assert pub_data["status"] == "Marked Published"
    assert pub_data["published_url"] == "https://instagram.com/p/lumo-summer-launch"


def test_high_risk_two_reviewer_requirement():
    creator_token = get_token("creator.social@lumo.internal")
    rev1_token = get_token("reviewer.sarah@lumo.internal")
    rev2_token = get_token("reviewer.alex@lumo.internal")

    h_creator = {"Authorization": f"Bearer {creator_token}"}
    h_rev1 = {"Authorization": f"Bearer {rev1_token}"}
    h_rev2 = {"Authorization": f"Bearer {rev2_token}"}

    # High-risk press release
    create_res = client.post(
        "/api/v1/submissions",
        json={
            "title": "Corporate Press Release",
            "channel": "press_release",
            "content": "Official announcement regarding global retail distribution expansion.",
        },
        headers=h_creator,
    )
    assert create_res.status_code == 200
    sub = create_res.json()
    assert sub["risk_tier"] == "high"
    sub_id = sub["id"]

    # Submit
    client.post(f"/api/v1/submissions/{sub_id}/review", headers=h_creator)
    client.post(f"/api/v1/submissions/{sub_id}/submit", headers=h_creator)
    client.post(f"/api/v1/submissions/{sub_id}/claim", headers=h_rev1)

    # 1st approval: should remain In Review because high-risk requires 2 distinct approvers
    app1_res = client.post(f"/api/v1/submissions/{sub_id}/approve", headers=h_rev1)
    assert app1_res.status_code == 200
    assert app1_res.json()["status"] == "In Review"

    # Same reviewer trying to approve again is rejected
    dup_app_res = client.post(f"/api/v1/submissions/{sub_id}/approve", headers=h_rev1)
    assert dup_app_res.status_code == 400

    # 2nd distinct reviewer approves -> moves to Approved
    app2_res = client.post(f"/api/v1/submissions/{sub_id}/approve", headers=h_rev2)
    assert app2_res.status_code == 200
    assert app2_res.json()["status"] == "Approved"
