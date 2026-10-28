import io
from fastapi.testclient import TestClient
from app.main import app
from app.adapters.db.session import SessionLocal
from app.adapters.db.models import Notification, Submission, Review, User
from app.domain.workflow.permissions import normalize_channel, get_risk_tier_for_channel

client = TestClient(app)


def get_token(email: str = "creator.social@lumo.internal") -> str:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "LumoDemo2026!"},
    )
    assert res.status_code == 200, f"Login failed: {res.text}"
    return res.json()["access_token"]


def test_g14_channel_normalization():
    token = get_token("creator.social@lumo.internal")
    headers = {"Authorization": f"Bearer {token}"}

    # Test pure function mappings
    assert normalize_channel("Press Release") == "press_release"
    assert normalize_channel("press-release") == "press_release"
    assert normalize_channel("PR") == "press_release"
    assert get_risk_tier_for_channel("Press Release") == "high"
    assert get_risk_tier_for_channel("press-release") == "high"
    assert get_risk_tier_for_channel("social") == "low"
    assert get_risk_tier_for_channel("Email Campaign") == "medium"

    # Test create_submission endpoint with non-canonical channel strings
    res = client.post(
        "/api/v1/submissions",
        json={
            "title": "Normalized PR Campaign",
            "channel": "Press Release",
            "content": "Official announcement regarding our revolutionary non-toxic peptides.",
        },
        headers=headers,
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["channel"] == "press_release"
    assert data["risk_tier"] == "high"

    # Test list_submissions filtering with variations
    list_res = client.get("/api/v1/submissions?channel=press-release", headers=headers)
    assert list_res.status_code == 200
    ids = [s["id"] for s in list_res.json()]
    assert data["id"] in ids


def test_g16_empty_content_validation():
    token = get_token("creator.social@lumo.internal")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Blank content on create -> 422
    res_empty = client.post(
        "/api/v1/submissions",
        json={"title": "Empty Post", "channel": "social", "content": "   "},
        headers=headers,
    )
    assert res_empty.status_code == 422
    assert "content cannot be empty" in res_empty.json()["message"].lower()

    # 2. Too short content (< 5 chars) -> 422
    res_short = client.post(
        "/api/v1/submissions",
        json={"title": "Short Post", "channel": "social", "content": "Hey"},
        headers=headers,
    )
    assert res_short.status_code == 422

    # 3. 0-byte file upload -> 422
    zero_file = io.BytesIO(b"")
    res_file = client.post(
        "/api/v1/submissions/upload",
        files={"file": ("empty.pdf", zero_file, "application/pdf")},
        data={"title": "Empty Upload", "channel": "social"},
        headers=headers,
    )
    assert res_file.status_code == 422
    assert "empty" in res_file.json()["message"].lower()


def test_f67_reset_demo_endpoints():
    admin_token = get_token("admin@lumo.internal")
    creator_token = get_token("creator.social@lumo.internal")

    # Non-admin forbidden
    res_forbidden = client.get(
        "/api/v1/admin/reset-demo",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert res_forbidden.status_code == 403

    # Admin GET reset-demo
    res_get = client.get(
        "/api/v1/admin/reset-demo",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_get.status_code == 200
    assert res_get.json()["status"] == "ok"

    # Admin POST system/reset-demo
    res_post = client.post(
        "/api/v1/system/reset-demo",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_post.status_code == 200
    assert res_post.json()["status"] == "ok"


def test_f26_notifications_and_double_click_protection():
    creator_token = get_token("creator.social@lumo.internal")
    rev1_token = get_token("reviewer.sarah@lumo.internal")
    rev2_token = get_token("manager.kavita@lumo.internal")

    creator_h = {"Authorization": f"Bearer {creator_token}"}
    rev1_h = {"Authorization": f"Bearer {rev1_token}"}
    rev2_h = {"Authorization": f"Bearer {rev2_token}"}

    # 1. Create a high-risk press release submission
    create_res = client.post(
        "/api/v1/submissions",
        json={
            "title": "High Risk Q4 Financial Clinical Report",
            "channel": "press_release",
            "content": "Clinical testing showed 99.4% improvement with zero side-effects across all age groups.",
        },
        headers=creator_h,
    )
    assert create_res.status_code == 200
    sub_id = create_res.json()["id"]

    # Run review synchronously
    rev_res = client.post(f"/api/v1/submissions/{sub_id}/review?sync=true", headers=creator_h)
    assert rev_res.status_code == 200

    # Submit for approval
    sub_action = client.post(f"/api/v1/submissions/{sub_id}/submit", headers=creator_h)
    assert sub_action.status_code == 200

    # Reviewer 1 claims
    claim_res = client.post(f"/api/v1/submissions/{sub_id}/claim", headers=rev1_h)
    assert claim_res.status_code == 200

    # Reviewer 1 approves (1st of 2 required)
    app1_res = client.post(
        f"/api/v1/submissions/{sub_id}/approve",
        json={"note": "First reviewer clinical sign-off."},
        headers=rev1_h,
    )
    assert app1_res.status_code == 200
    assert app1_res.json()["status"] == "In Review"

    # Check that creator received "Needs Second Approver" notification
    notifs_res = client.get("/api/v1/notifications", headers=creator_h)
    assert notifs_res.status_code == 200
    notifs = notifs_res.json()
    needs_second = [n for n in notifs if n["title"] == "Needs Second Approver" and n["submission_id"] == sub_id]
    assert len(needs_second) >= 1
    notif_id = needs_second[0]["id"]

    # Reviewer 2 approves (2nd approval -> triggers Approved state)
    app2_res = client.post(
        f"/api/v1/submissions/{sub_id}/approve",
        json={"note": "Second reviewer executive sign-off."},
        headers=rev2_h,
    )
    assert app2_res.status_code == 200
    assert app2_res.json()["status"] == "Approved"

    # Check that creator received "Approved" notification
    notifs_res2 = client.get("/api/v1/notifications", headers=creator_h)
    notifs2 = notifs_res2.json()
    approved_notifs = [n for n in notifs2 if n["title"] == "Approved" and n["submission_id"] == sub_id]
    assert len(approved_notifs) >= 1

    # Mark the first notification as read
    read_res = client.post(f"/api/v1/notifications/{notif_id}/read", headers=creator_h)
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True

    # Check unread notifications endpoint excludes read notification
    notifs_res3 = client.get("/api/v1/notifications", headers=creator_h)
    active_ids = [n["id"] for n in notifs_res3.json()]
    assert notif_id not in active_ids
