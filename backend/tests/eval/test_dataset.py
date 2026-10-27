"""
Automated validation of the 84-document evaluation dataset.
Verifies schema conformity, unique IDs, KB entry grounding, span accuracy,
and required test coverage across channels, rule types, and claim verdicts.
"""

import pytest
from app.eval.loader import load_dataset
from app.seed.lumo_brand import (
    SEED_TERMS,
    SEED_RULES,
    SEED_FACTS,
    SEED_TONE,
    SEED_ASSETS,
)


@pytest.fixture(scope="module")
def dataset():
    return load_dataset()


@pytest.fixture(scope="module")
def kb_codes():
    all_entries = SEED_TERMS + SEED_RULES + SEED_FACTS + SEED_TONE + SEED_ASSETS
    return {entry["code"] for entry in all_entries if "code" in entry}


def test_dataset_count_and_uniqueness(dataset):
    # Requirement: 60 to 100 synthetic documents
    assert 60 <= len(dataset) <= 100
    assert len(dataset) == 84

    # No duplicate document IDs
    doc_ids = [d.id for d in dataset]
    assert len(doc_ids) == len(set(doc_ids))


def test_dataset_clean_ratio(dataset):
    clean_docs = [d for d in dataset if d.is_clean]
    ratio = len(clean_docs) / len(dataset)
    # Requirement: roughly 25% clean
    assert 0.20 <= ratio <= 0.30
    assert len(clean_docs) == 21
    assert pytest.approx(ratio, rel=1e-2) == 0.25


def test_every_expected_entry_code_in_kb(dataset, kb_codes):
    for doc in dataset:
        for f in doc.expected_findings:
            assert f.entry_code in kb_codes, (
                f"Document '{doc.id}' references non-existent KB code '{f.entry_code}'"
            )


def test_every_finding_span_exact_match(dataset):
    """Asserts that text[span_start:span_end] exactly matches excerpt for 100% of findings."""
    for doc in dataset:
        for f in doc.expected_findings:
            actual_slice = doc.text[f.span_start : f.span_end]
            assert actual_slice == f.excerpt, (
                f"Document '{doc.id}' span mismatch for '{f.entry_code}': "
                f"expected '{f.excerpt}', got '{actual_slice}' at [{f.span_start}:{f.span_end}]"
            )


def test_channel_coverage(dataset):
    channels = {d.channel for d in dataset}
    expected_channels = {"social", "email", "blog", "web", "press_release"}
    assert expected_channels.issubset(channels)


def test_claim_verdicts_coverage(dataset):
    verdicts = {
        f.verdict
        for d in dataset
        for f in doc_findings(d)
        if f.verdict is not None
    }
    expected_verdicts = {"Supported", "Contradicted", "Unverified", "Expired"}
    assert expected_verdicts.issubset(verdicts)


def test_adversarial_and_near_miss_coverage(dataset):
    notes_and_titles = " ".join((d.notes or "") + " " + d.title for d in dataset).lower()
    assert "hair serum" in notes_and_titles or "exception" in notes_and_titles
    assert "prompt injection" in notes_and_titles or "adversarial" in notes_and_titles
    assert "expired" in notes_and_titles
    assert "confidential" in notes_and_titles


def doc_findings(doc):
    return doc.expected_findings
