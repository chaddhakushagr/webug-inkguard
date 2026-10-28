"""
Unit and integration tests for Image Submissions and Visual Compliance Checks.
Tests:
1. on-palette image (no palette finding)
2. off-palette image (palette finding)
3. image with the logo (logo_present)
4. image without logo (no_logo_found)
5. oversized image (422 for dimensions > 4096 and size > 5MB)
6. corrupted image (422)
7. unsupported format (422)
8. OCR graceful degradation (when tesseract is unavailable)
All test fixtures are generated programmatically with Pillow — zero binary files checked in.
"""

import io
import os
import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

from app.config import settings
from app.adapters.db.session import engine, Base
from app.adapters.documents.image_extractor import (
    ImageExtractor,
    ensure_lumo_logo_exists,
    DEFAULT_BRAND_COLOURS,
    FALLBACK_OCR_TEXT,
)
from app.adapters.documents.extractor import DocumentExtractor
from app.domain.documents.models import DocumentValidationError
from app.main import app

# Ensure DB schema is available
Base.metadata.create_all(bind=engine)
client = TestClient(app)


# --- Programmatic Fixture Generators (Zero binary files checked in) ---

def make_on_palette_image_bytes() -> bytes:
    """Generate a 200x100 PNG using only approved Lumo brand colors."""
    img = Image.new("RGB", (200, 100), color="#1A3C34")  # Deep Teal
    d = ImageDraw.Draw(img)
    d.rectangle([20, 20, 180, 80], fill="#F5F0E8")  # Warm Cream
    d.rectangle([40, 35, 160, 65], fill="#D4A853")  # Gold
    d.text((50, 45), "LUMO BEAUTY", fill="#FFFFFF")  # White
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_off_palette_image_bytes() -> bytes:
    """Generate a 200x100 PNG containing unapproved colors (bright red #FF0000)."""
    img = Image.new("RGB", (200, 100), color="#FF0000")  # Bright Red (delta-E ~77.7 to brand)
    d = ImageDraw.Draw(img)
    d.rectangle([20, 20, 180, 80], fill="#00FF00")  # Neon Green
    d.text((50, 45), "UNAPPROVED", fill="#0000FF")   # Blue
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_image_with_logo_bytes() -> bytes:
    """Generate image matching the approved Lumo logo asset."""
    logo_path = ensure_lumo_logo_exists()
    with Image.open(logo_path) as logo:
        buf = io.BytesIO()
        logo.save(buf, format="PNG")
        return buf.getvalue()


def make_image_without_logo_bytes() -> bytes:
    """Generate an image with no Lumo logo (distance > 20)."""
    img = Image.new("RGB", (200, 200), color="#F5F0E8")
    d = ImageDraw.Draw(img)
    d.ellipse([30, 30, 170, 170], fill="#1A3C34")
    d.ellipse([60, 60, 140, 140], fill="#D4A853")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_oversized_dimension_image_bytes() -> bytes:
    """Generate an image exceeding the 4096x4096 dimension limit."""
    img = Image.new("RGB", (4097, 10), color="#1A3C34")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_corrupted_image_bytes() -> bytes:
    """Generate bytes with valid PNG magic bytes followed by corrupted garbage."""
    return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRcorrupted_garbage_payload_123456789"


def make_unsupported_format_bytes() -> bytes:
    """Generate bytes of an unsupported format (BMP magic bytes b'BM')."""
    return b"BM\x00\x00\x00\x00\x00\x00\x00\x00\x36\x00\x00\x00\x28\x00\x00\x00" + b"\x00" * 60


def get_creator_auth():
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "creator.social@lumo.internal", "password": settings.DEMO_PASSWORD},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# --- Unit Tests ---

def test_on_palette_image_no_palette_finding():
    """Verify on-palette image produces on_palette verdict and NO PALETTE-001 finding."""
    img_bytes = make_on_palette_image_bytes()
    extractor = ImageExtractor()
    doc = extractor.extract(img_bytes, "on_palette.png")

    assert doc.format == "image"
    assert doc.palette_verdict == "on_palette"
    palette_findings = [f for f in doc.visual_findings if f.get("cited_entry_code") == "PALETTE-001"]
    assert len(palette_findings) == 0, f"Expected 0 palette findings, got: {palette_findings}"


def test_off_palette_image_emits_palette_finding():
    """Verify off-palette image produces off_palette verdict and cites PALETTE-001."""
    img_bytes = make_off_palette_image_bytes()
    extractor = ImageExtractor()
    doc = extractor.extract(img_bytes, "off_palette.png")

    assert doc.format == "image"
    assert doc.palette_verdict == "off_palette"
    palette_findings = [f for f in doc.visual_findings if f.get("cited_entry_code") == "PALETTE-001"]
    assert len(palette_findings) >= 1
    pf = palette_findings[0]
    assert pf["issue_type"] == "brand"
    assert "Off-palette color" in pf["excerpt"]
    assert "delta-E" in pf["excerpt"]


def test_image_with_logo_detects_logo_present():
    """Verify submitted image with approved logo produces logo_present verdict."""
    img_bytes = make_image_with_logo_bytes()
    extractor = ImageExtractor()
    doc = extractor.extract(img_bytes, "with_logo.png")

    assert doc.format == "image"
    assert doc.logo_verdict == "logo_present"
    logo_findings = [f for f in doc.visual_findings if f.get("cited_entry_code") == "ASSET-LOGO-01"]
    assert len(logo_findings) == 1
    lf = logo_findings[0]
    assert lf["excerpt"] == "logo_present"
    assert lf["severity"] == "low"  # Non-blocking advisory
    assert lf["is_policy"] is False


def test_image_without_logo_detects_no_logo_found():
    """Verify submitted image without logo produces no_logo_found verdict."""
    img_bytes = make_image_without_logo_bytes()
    extractor = ImageExtractor()
    doc = extractor.extract(img_bytes, "no_logo.png")

    assert doc.format == "image"
    assert doc.logo_verdict == "no_logo_found"
    logo_findings = [f for f in doc.visual_findings if f.get("cited_entry_code") == "ASSET-LOGO-01"]
    assert len(logo_findings) == 1
    lf = logo_findings[0]
    assert lf["excerpt"] == "no_logo_found"
    assert lf["severity"] == "low"


def test_oversized_dimensions_rejected_with_422():
    """Verify image exceeding 4096 dimension limit is rejected with HTTP 422."""
    img_bytes = make_oversized_dimension_image_bytes()
    extractor = DocumentExtractor()
    with pytest.raises(DocumentValidationError) as exc_info:
        extractor.extract(img_bytes, "huge_dim.png")
    assert "exceed maximum allowed dimension of 4096x4096" in str(exc_info.value.message)


def test_oversized_filesize_rejected_with_422():
    """Verify image exceeding 5 MB size cap is rejected with HTTP 422."""
    # 5 MB + 100 bytes
    large_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * (5 * 1024 * 1024 + 100)
    extractor = DocumentExtractor()
    with pytest.raises(DocumentValidationError) as exc_info:
        extractor.extract(large_bytes, "huge_file.png")
    assert "5 MB" in str(exc_info.value.message)


def test_decompression_bomb_guard_returns_422():
    """Verify Pillow DecompressionBombError is caught and converted to 422 plain message."""
    from unittest.mock import patch
    extractor = ImageExtractor()
    with patch("PIL.Image.open") as mock_open:
        mock_open.side_effect = Image.DecompressionBombError("Decompression bomb detected")
        with pytest.raises(DocumentValidationError) as exc_info:
            extractor.extract(b"\x89PNG\r\n\x1a\n1234", "bomb.png")
        assert "decompression bomb threshold" in str(exc_info.value.message).lower()


def test_corrupted_image_rejected_with_422():
    """Verify corrupted image bytes raise DocumentValidationError (HTTP 422)."""
    corrupt_bytes = make_corrupted_image_bytes()
    extractor = DocumentExtractor()
    with pytest.raises(DocumentValidationError) as exc_info:
        extractor.extract(corrupt_bytes, "corrupt.png")
    assert "corrupted" in str(exc_info.value.message).lower()


def test_unsupported_format_rejected_with_422():
    """Verify unsupported image format (e.g. BMP) is rejected with plain 422 message."""
    unsupported_bytes = make_unsupported_format_bytes()
    extractor = DocumentExtractor()
    with pytest.raises(DocumentValidationError) as exc_info:
        extractor.extract(unsupported_bytes, "image.bmp")
    assert "Invalid file format: Magic bytes signature does not match supported formats" in str(exc_info.value.message)


def test_ocr_graceful_degradation():
    """Verify clean degradation when tesseract is unavailable on the host."""
    img_bytes = make_on_palette_image_bytes()
    extractor = ImageExtractor()
    doc = extractor.extract(img_bytes, "degrade.png")

    # If tesseract is absent on this host, verify graceful degradation
    import shutil
    if not shutil.which("tesseract"):
        assert doc.ocr_applied is False
        assert doc.full_text == FALLBACK_OCR_TEXT
        assert "OCR unavailable on this host" in (doc.ocr_limitation or "")
        # Palette and logo checks still ran
        assert doc.palette_verdict == "on_palette"
        assert doc.logo_verdict is not None


# --- End-to-End API Integration Tests (POST /api/v1/submissions/upload) ---

def test_api_upload_on_palette_image():
    """API upload of on-palette image succeeds, records upload_image source, and has no palette finding."""
    auth = get_creator_auth()
    img_bytes = make_on_palette_image_bytes()

    files = {"file": ("banner.png", img_bytes, "image/png")}
    data = {"channel": "social", "title": "Summer Campaign Banner", "sync_review": "true"}

    res = client.post("/api/v1/submissions/upload", files=files, data=data, headers=auth)
    assert res.status_code == 200, res.text
    sub = res.json()
    assert sub["title"] == "Summer Campaign Banner"
    sub_id = sub["id"]

    # Verify findings via API
    f_res = client.get(f"/api/v1/submissions/{sub_id}/findings", headers=auth)
    assert f_res.status_code == 200
    findings = f_res.json()

    # Ensure NO palette violation finding exists
    palette_findings = [f for f in findings if f.get("cited_entry_code") == "PALETTE-001"]
    assert len(palette_findings) == 0

    # Ensure advisory logo finding is present and non-blocking
    logo_findings = [f for f in findings if f.get("cited_entry_code") == "ASSET-LOGO-01"]
    assert len(logo_findings) >= 1
    assert logo_findings[0]["severity"] == "low"


def test_api_upload_off_palette_image():
    """API upload of off-palette image succeeds and emits PALETTE-001 finding."""
    auth = get_creator_auth()
    img_bytes = make_off_palette_image_bytes()

    files = {"file": ("neon_banner.png", img_bytes, "image/png")}
    data = {"channel": "social", "title": "Neon Off Palette Banner", "sync_review": "true"}

    res = client.post("/api/v1/submissions/upload", files=files, data=data, headers=auth)
    assert res.status_code == 200, res.text
    sub = res.json()
    sub_id = sub["id"]

    # Verify findings via API
    f_res = client.get(f"/api/v1/submissions/{sub_id}/findings", headers=auth)
    assert f_res.status_code == 200
    findings = f_res.json()

    # Ensure PALETTE-001 finding is present
    palette_findings = [f for f in findings if f.get("cited_entry_code") == "PALETTE-001"]
    assert len(palette_findings) >= 1
    assert palette_findings[0]["issue_type"] == "brand"
    assert palette_findings[0]["location"] == "Image Palette"


def test_api_upload_with_logo_image():
    """API upload of image with logo detects logo_present advisory finding."""
    auth = get_creator_auth()
    img_bytes = make_image_with_logo_bytes()

    files = {"file": ("lumo_logo_upload.png", img_bytes, "image/png")}
    data = {"channel": "web", "title": "Lumo Logo Asset", "sync_review": "true"}

    res = client.post("/api/v1/submissions/upload", files=files, data=data, headers=auth)
    assert res.status_code == 200, res.text
    sub_id = res.json()["id"]

    f_res = client.get(f"/api/v1/submissions/{sub_id}/findings", headers=auth)
    assert f_res.status_code == 200
    findings = f_res.json()

    logo_findings = [f for f in findings if f.get("cited_entry_code") == "ASSET-LOGO-01"]
    assert len(logo_findings) == 1
    assert logo_findings[0]["excerpt"] == "logo_present"
    assert logo_findings[0]["severity"] == "low"


def test_api_upload_oversized_dimensions_returns_422():
    """API upload of oversized dimension image returns HTTP 422 with plain message."""
    auth = get_creator_auth()
    img_bytes = make_oversized_dimension_image_bytes()

    files = {"file": ("too_large_dim.png", img_bytes, "image/png")}
    res = client.post("/api/v1/submissions/upload", files=files, headers=auth)
    assert res.status_code == 422
    err_msg = res.json().get("message") or res.json().get("detail") or ""
    assert "exceed maximum allowed dimension of 4096x4096" in err_msg


def test_api_upload_corrupted_image_returns_422():
    """API upload of corrupted image returns HTTP 422 with plain message."""
    auth = get_creator_auth()
    img_bytes = make_corrupted_image_bytes()

    files = {"file": ("corrupt.png", img_bytes, "image/png")}
    res = client.post("/api/v1/submissions/upload", files=files, headers=auth)
    assert res.status_code == 422
    err_msg = res.json().get("message") or res.json().get("detail") or ""
    assert "corrupted" in err_msg.lower()


def test_api_upload_unsupported_format_returns_422():
    """API upload of unsupported format returns HTTP 422 with plain message."""
    auth = get_creator_auth()
    unsupported_bytes = make_unsupported_format_bytes()

    files = {"file": ("test.bmp", unsupported_bytes, "image/bmp")}
    res = client.post("/api/v1/submissions/upload", files=files, headers=auth)
    assert res.status_code == 422
    err_msg = res.json().get("message") or res.json().get("detail") or ""
    assert "Invalid file format: Magic bytes signature does not match supported formats" in err_msg
