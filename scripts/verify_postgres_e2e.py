import httpx
import time

BASE = "http://127.0.0.1:8080/api/v1"

# 1. Login as Creator
res = httpx.post(f"{BASE}/auth/login", json={"email": "creator.social@lumo.internal", "password": "LumoDemo2026!"})
assert res.status_code == 200, f"Creator login failed: {res.text}"
creator_token = res.json()["access_token"]
headers_c = {"Authorization": f"Bearer {creator_token}"}
print("GP-1 Creator login: PASS")

# 2. Create Submission
res = httpx.post(
    f"{BASE}/submissions",
    headers=headers_c,
    json={
        "title": "Postgres Deployment Golden Path Press Release",
        "channel": "press_release",
        "content": "Experience our new hydrating serum with cold-pressed rosehip seed extract.",
    }
)
assert res.status_code == 200, f"Create submission failed: {res.text}"
sub_data = res.json()
sub_id = sub_data["id"]
sub_status = sub_data["status"]
risk_tier = sub_data["risk_tier"]
print(f"GP-2 Create Submission: PASS (id={sub_id}, status={sub_status}, risk_tier={risk_tier})")

# 3. Run Review
res = httpx.post(f"{BASE}/submissions/{sub_id}/review", headers=headers_c)
assert res.status_code == 200, f"Run review failed: {res.text}"
rev_data = res.json()
rev_id = rev_data.get("id") or rev_data.get("review_id")
print(f"GP-3 Run Review: PASS (review_id={rev_id})")

# Wait for review background task to complete and set submission to Checked
for _ in range(20):
    sub_res = httpx.get(f"{BASE}/submissions/{sub_id}", headers=headers_c)
    if sub_res.json()["status"] == "Checked":
        break
    time.sleep(0.5)

assert sub_res.json()["status"] == "Checked", f"Expected Checked, got {sub_res.json()['status']}"
print("GP-3 Review Completed: PASS (status=Checked)")

# 3b. Resolve any open high-severity findings
findings_res = httpx.get(f"{BASE}/submissions/{sub_id}/findings", headers=headers_c)
assert findings_res.status_code == 200
for f in findings_res.json():
    if f["severity"] == "high" and f["status"] == "open":
        dismiss_res = httpx.post(
            f"{BASE}/findings/{f['id']}/dismiss",
            json={"reason_code": "editorial_exception", "reason_text": "Authorized marketing exception for campaign launch."},
            headers=headers_c,
        )
        assert dismiss_res.status_code == 200

# 4. Submit for Approval
res = httpx.post(f"{BASE}/submissions/{sub_id}/submit", headers=headers_c)
assert res.status_code == 200, f"Submit for approval failed: {res.text}"
print("GP-4 Submit for Approval: PASS (status=Submitted)")

# 5. Reviewer 1 Claim & Approve
res = httpx.post(f"{BASE}/auth/login", json={"email": "reviewer.sarah@lumo.internal", "password": "LumoDemo2026!"})
assert res.status_code == 200
r1_token = res.json()["access_token"]
headers_r1 = {"Authorization": f"Bearer {r1_token}"}

res = httpx.post(f"{BASE}/submissions/{sub_id}/claim", headers=headers_r1)
assert res.status_code == 200
print("GP-5 Claim by Reviewer 1: PASS (status=In Review)")

res = httpx.post(f"{BASE}/submissions/{sub_id}/approve", headers=headers_r1, json={"comment": "First approval on high-risk copy"})
assert res.status_code == 200
status_after_first = res.json()["status"]
print(f"GP-5 First Approval: PASS (status={status_after_first})")

# 6. Reviewer 2 Second Approval (for high-risk press_release)
if status_after_first != "Approved":
    res = httpx.post(f"{BASE}/auth/login", json={"email": "reviewer.alex@lumo.internal", "password": "LumoDemo2026!"})
    assert res.status_code == 200
    r2_token = res.json()["access_token"]
    headers_r2 = {"Authorization": f"Bearer {r2_token}"}

    res = httpx.post(f"{BASE}/submissions/{sub_id}/approve", headers=headers_r2, json={"comment": "Second approval on high-risk copy"})
    assert res.status_code == 200
    final_status = res.json()["status"]
    assert final_status == "Approved", f"Expected Approved, got {final_status}"
    print(f"GP-5 Second Approval: PASS (status={final_status})")
else:
    print("GP-5 Approval: PASS (status=Approved)")

# 7. Publish
res = httpx.post(f"{BASE}/submissions/{sub_id}/mark-published", headers=headers_c, json={"url": "https://lumo.example.com/pr/golden-path-postgres"})
assert res.status_code == 200, f"Mark published failed: {res.text}"
pub_status = res.json()["status"]
assert pub_status == "Marked Published"
print(f"GP-6 Mark Published: PASS (status={pub_status})")
print("\n>>> FULL GOLDEN PATH PASSED ON POSTGRESQL PRODUCTION DEPLOYABLE <<<")
