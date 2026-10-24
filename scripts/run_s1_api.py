"""
Run Sample S1 through the live API in mock mode,
and output the review, findings, and boundary JSON.
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

def main():
    # 1. Login as creator
    login_res = client.post("/api/v1/auth/login", json={"email": "creator.social@lumo.internal", "password": settings.DEMO_PASSWORD})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Ingest Sample S1
    s1_content = (
        "Discover the miracle powers of our new age-smart serum! Clinically proven to completely cure dry skin "
        "and give you flawless radiance in just 2 days. Don't wait—our guaranteed #1 formula delivers 100% satisfaction."
    )
    create_res = client.post(
        "/api/v1/submissions",
        json={
            "title": "S1: Spring Hydration Campaign (Unsupported & Contradicted Claims)",
            "channel": "social",
            "content": s1_content,
        },
        headers=headers,
    )
    assert create_res.status_code == 200
    sub_id = create_res.json()["id"]

    # 3. Trigger review in mock mode
    rev_trigger_res = client.post(f"/api/v1/submissions/{sub_id}/review?sync=true", headers=headers)
    assert rev_trigger_res.status_code == 200
    review_record = rev_trigger_res.json()
    review_id = review_record["id"]

    # 4. Fetch Review record
    rev_res = client.get(f"/api/v1/reviews/{review_id}", headers=headers)
    assert rev_res.status_code == 200
    review_data = rev_res.json()

    # 5. Fetch Findings
    findings_res = client.get(f"/api/v1/submissions/{sub_id}/findings", headers=headers)
    assert findings_res.status_code == 200
    findings_data = findings_res.json()

    # 6. Fetch Data Boundary
    boundary_res = client.get(f"/api/v1/reviews/{review_id}/boundary", headers=headers)
    assert boundary_res.status_code == 200
    boundary_data = boundary_res.json()

    print("=== SAMPLE S1 REVIEW JSON ===")
    print(json.dumps(review_data, indent=2))

    print("\n=== SAMPLE S1 FINDINGS JSON ===")
    print(json.dumps(findings_data, indent=2))

    print("\n=== SAMPLE S1 DATA BOUNDARY JSON ===")
    print(json.dumps(boundary_data, indent=2))

if __name__ == "__main__":
    main()
