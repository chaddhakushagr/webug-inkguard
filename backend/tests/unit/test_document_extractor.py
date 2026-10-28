"""
Unit tests for Document Extractor and Safety Validator.
Verifies:
- Magic bytes detection and executable rejection.
- Size caps, entry count limits, and zip bomb guards.
- DOCX parsing (headings, links, images, alt text, tables, contrast).
- PDF parsing (text per page, page count, scanned detection, title).
"""

import os
import pytest
from app.adapters.documents.validator import validate_document_safety
from app.adapters.documents.extractor import DocumentExtractor
from app.domain.documents.models import DocumentValidationError

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../fixtures/documents"))


def test_validator_rejects_empty_file():
    with pytest.raises(DocumentValidationError) as exc:
        validate_document_safety(b"", "empty.docx")
    assert "empty" in exc.value.message.lower()


def test_validator_rejects_executable():
    exe_path = os.path.join(FIXTURES_DIR, "renamed_exe.docx")
    with open(exe_path, "rb") as f:
        data = f.read()
    with pytest.raises(DocumentValidationError) as exc:
        validate_document_safety(data, "renamed_exe.docx")
    assert "executable binary detected" in exc.value.message.lower()


def test_validator_rejects_oversize_file():
    oversize_path = os.path.join(FIXTURES_DIR, "oversize.docx")
    with open(oversize_path, "rb") as f:
        data = f.read()
    with pytest.raises(DocumentValidationError) as exc:
        validate_document_safety(data, "oversize.docx")
    assert "5 mb" in exc.value.message.lower()


def test_validator_rejects_zip_bomb():
    bomb_path = os.path.join(FIXTURES_DIR, "zip_bomb.docx")
    with open(bomb_path, "rb") as f:
        data = f.read()
    with pytest.raises(DocumentValidationError) as exc:
        validate_document_safety(data, "zip_bomb.docx")
    assert "zip bomb" in exc.value.message.lower()


def test_validator_rejects_corrupted_file():
    corrupted_path = os.path.join(FIXTURES_DIR, "corrupted.docx")
    with open(corrupted_path, "rb") as f:
        data = f.read()
    with pytest.raises(DocumentValidationError) as exc:
        validate_document_safety(data, "corrupted.docx")
    assert "corrupted" in exc.value.message.lower()


def test_docx_extractor_good_file():
    good_path = os.path.join(FIXTURES_DIR, "good.docx")
    with open(good_path, "rb") as f:
        data = f.read()
    
    extractor = DocumentExtractor()
    doc = extractor.extract(data, "good.docx")

    assert doc.format == "docx"
    assert "Lumo Botanical Daily Skincare Manual" in doc.full_text
    assert len(doc.blocks) >= 3
    
    # Check heading levels
    headings = [b for b in doc.blocks if b.block_type == "heading"]
    assert len(headings) >= 2
    assert headings[0].level == 1
    assert headings[1].level == 2

    # Check images and alt text
    assert len(doc.images) == 1
    assert doc.images[0].has_alt_text is True
    assert "Serum Bottle" in doc.images[0].alt_text

    # Check descriptive link
    assert len(doc.links) == 1
    assert "catalogue" in doc.links[0].text

    # Check tables
    assert len(doc.tables) == 1
    assert doc.tables[0].rows == 2
    assert doc.tables[0].cols == 2


def test_docx_extractor_bad_a11y_file():
    bad_path = os.path.join(FIXTURES_DIR, "bad_a11y.docx")
    with open(bad_path, "rb") as f:
        data = f.read()

    extractor = DocumentExtractor()
    doc = extractor.extract(data, "bad_a11y.docx")

    assert doc.format == "docx"
    
    # Image missing alt text
    assert len(doc.images) == 1
    assert doc.images[0].has_alt_text is False

    # Heading skip H1 -> H3
    headings = [b for b in doc.blocks if b.block_type == "heading"]
    levels = [h.level for h in headings]
    assert 1 in levels
    assert 3 in levels

    # "Click here" link
    assert len(doc.links) >= 1
    assert doc.links[0].text.lower() == "click here"

    # Low contrast runs
    assert len(doc.low_contrast_runs) >= 1
    assert doc.low_contrast_runs[0]["contrast_ratio"] < 4.5


def test_pdf_extractor_text_file():
    pdf_path = os.path.join(FIXTURES_DIR, "text.pdf")
    with open(pdf_path, "rb") as f:
        data = f.read()

    extractor = DocumentExtractor()
    doc = extractor.extract(data, "text.pdf")

    assert doc.format == "pdf"
    assert doc.page_count == 1
    assert "Lumo Botanical Skincare Formulation Guide" in doc.full_text
    assert doc.is_scanned is False
    assert doc.title == "Lumo Botanical Skincare Formulation Guide"


def test_pdf_extractor_scanned_file():
    scanned_path = os.path.join(FIXTURES_DIR, "scanned.pdf")
    with open(scanned_path, "rb") as f:
        data = f.read()

    extractor = DocumentExtractor()
    doc = extractor.extract(data, "scanned.pdf")

    assert doc.format == "pdf"
    assert doc.is_scanned is True
    assert doc.ocr_limitation is not None
    assert "OCR unavailable on this host" in doc.ocr_limitation
