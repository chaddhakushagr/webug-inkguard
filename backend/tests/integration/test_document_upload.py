"""
Integration tests for document submission and accessibility checking.
Tests all 8 document fixtures:
1. good.docx (valid docx, location tracking, storage download)
2. bad_a11y.docx (a11y checks: alt text, heading skips, click here, empty headings, contrast)
3. text.pdf (text pdf, page extraction, metadata title)
4. scanned.pdf (scanned detection, declared OCR limitation)
5. corrupted.docx (returns HTTP 422 plain message)
6. renamed_exe.docx (magic bytes rejection, returns HTTP 422)
7. oversize.docx (size cap > 5MB, returns HTTP 422)
8. zip_bomb.docx (zip bomb protection, returns HTTP 422)
"""

import os
from fastapi.testclient import TestClient
from app.config import settings
from app.adapters.db.session import engine, Base
from app.adapters.db import models as db_models
from app.main import app

# Ensure DB schema is up to date for test runner
Base.metadata.create_all(bind=engine)

client = TestClient(app)
FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../fixtures/documents"))


def get_creator_auth():
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "creator.social@lumo.internal", "password": settings.DEMO_PASSWORD},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_upload_good_docx():
    auth = get_creator_auth()
    file_path = os.path.join(FIXTURES_DIR, "good.docx")
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    files = {"file": ("good.docx", file_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    data = {"channel": "web", "title": "Good DOCX Submission"}

    res = client.post("/api/v1/submissions/upload", files=files, data=data, headers=auth)
    assert res.status_code == 200, res.text
    sub = res.json()
    assert sub["title"] == "Good DOCX Submission"
    assert sub["status"] == "Draft"
    assert "Lumo Botanical Daily Skincare Manual" in sub["content"]
    sub_id = sub["id"]

    # Trigger review to verify finding location mapping
    rev_res = client.post(f"/api/v1/submissions/{sub_id}/review?sync=true", headers=auth)
    assert rev_res.status_code == 200

    # Verify download of original upload
    doc_res = client.get(f"/api/v1/submissions/{sub_id}/document", headers=auth)
    assert doc_res.status_code == 200
    assert doc_res.content == file_bytes
    assert 'attachment; filename="good.docx"' in doc_res.headers.get("content-disposition", "")


def test_upload_bad_a11y_docx():
    auth = get_creator_auth()
    file_path = os.path.join(FIXTURES_DIR, "bad_a11y.docx")
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    files = {"file": ("bad_a11y.docx", file_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    data = {"channel": "web", "sync_review": "true"}

    res = client.post("/api/v1/submissions/upload", files=files, data=data, headers=auth)
    assert res.status_code == 200, res.text
    sub = res.json()
    sub_id = sub["id"]

    # Check findings
    findings_res = client.get(f"/api/v1/submissions/{sub_id}/findings", headers=auth)
    assert findings_res.status_code == 200
    findings = findings_res.json()
    assert len(findings) > 0

    cited_rules = {f.get("cited_entry_code") for f in findings if f.get("cited_entry_code")}

    # Must detect:
    # 1. Missing alt text (RULE-A11Y-02)
    assert "RULE-A11Y-02" in cited_rules, f"Expected RULE-A11Y-02 in {cited_rules}"
    # 2. Heading skips (RULE-A11Y-03)
    assert "RULE-A11Y-03" in cited_rules, f"Expected RULE-A11Y-03 in {cited_rules}"
    # 3. Empty heading (RULE-A11Y-04)
    assert "RULE-A11Y-04" in cited_rules, f"Expected RULE-A11Y-04 in {cited_rules}"
    # 4. Click here link (RULE-A11Y-01)
    assert "RULE-A11Y-01" in cited_rules, f"Expected RULE-A11Y-01 in {cited_rules}"
    # 5. Low contrast run (RULE-A11Y-05)
    assert "RULE-A11Y-05" in cited_rules, f"Expected RULE-A11Y-05 in {cited_rules}"

    # Verify every finding has a valid location label
    for f in findings:
        assert f.get("location") is not None, f"Finding {f['id']} missing location: {f}"
        assert len(f["location"].strip()) > 0


def test_upload_text_pdf():
    auth = get_creator_auth()
    file_path = os.path.join(FIXTURES_DIR, "text.pdf")
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    files = {"file": ("text.pdf", file_bytes, "application/pdf")}
    data = {"channel": "blog"}

    res = client.post("/api/v1/submissions/upload", files=files, data=data, headers=auth)
    assert res.status_code == 200, res.text
    sub = res.json()
    assert "Lumo Botanical Skincare Formulation Guide" in sub["title"]
    assert "rosehip seed extract" in sub["content"]
    sub_id = sub["id"]

    # Verify content version records source type "upload_pdf"
    versions_res = client.get(f"/api/v1/submissions/{sub_id}/versions", headers=auth)
    assert versions_res.status_code == 200
    versions = versions_res.json()
    assert len(versions) >= 1
    assert versions[0]["source"] == "upload_pdf"

    # Verify document download
    doc_res = client.get(f"/api/v1/submissions/{sub_id}/document", headers=auth)
    assert doc_res.status_code == 200
    assert doc_res.content == file_bytes


def test_upload_scanned_pdf():
    auth = get_creator_auth()
    file_path = os.path.join(FIXTURES_DIR, "scanned.pdf")
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    files = {"file": ("scanned.pdf", file_bytes, "application/pdf")}
    data = {"channel": "press_release"}

    res = client.post("/api/v1/submissions/upload", files=files, data=data, headers=auth)
    assert res.status_code == 200, res.text
    sub = res.json()
    # Content declares limitation clearly
    assert "OCR unavailable on this host" in sub["content"] or "Scanned PDF" in sub["content"]


def test_upload_corrupted_file():
    auth = get_creator_auth()
    file_path = os.path.join(FIXTURES_DIR, "corrupted.docx")
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    files = {"file": ("corrupted.docx", file_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    res = client.post("/api/v1/submissions/upload", files=files, headers=auth)
    assert res.status_code == 422
    err_text = (res.json().get("message") or res.json().get("detail", "")).lower()
    assert "corrupted" in err_text or "archive" in err_text


def test_upload_renamed_exe():
    auth = get_creator_auth()
    file_path = os.path.join(FIXTURES_DIR, "renamed_exe.docx")
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    files = {"file": ("renamed_exe.docx", file_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    res = client.post("/api/v1/submissions/upload", files=files, headers=auth)
    assert res.status_code == 422
    err_text = (res.json().get("message") or res.json().get("detail", "")).lower()
    assert "executable binary detected" in err_text


def test_upload_oversize_file():
    auth = get_creator_auth()
    file_path = os.path.join(FIXTURES_DIR, "oversize.docx")
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    files = {"file": ("oversize.docx", file_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    res = client.post("/api/v1/submissions/upload", files=files, headers=auth)
    assert res.status_code == 422
    err_text = (res.json().get("message") or res.json().get("detail", "")).lower()
    assert "5 mb" in err_text


def test_upload_zip_bomb():
    auth = get_creator_auth()
    file_path = os.path.join(FIXTURES_DIR, "zip_bomb.docx")
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    files = {"file": ("zip_bomb.docx", file_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    res = client.post("/api/v1/submissions/upload", files=files, headers=auth)
    assert res.status_code == 422
    err_text = (res.json().get("message") or res.json().get("detail", "")).lower()
    assert "zip bomb" in err_text
