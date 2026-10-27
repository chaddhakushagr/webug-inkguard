"""
Unit tests for evaluation metrics and matching logic.
Tests hand-computed small cases to mathematically prove precision, recall, F1,
span overlap calculations, and verdict matching accuracy.
"""

import pytest
from app.eval.schema import ExpectedFinding, EvalDocument
from app.eval.metrics import (
    spans_overlap,
    finding_matches,
    compute_eval_metrics,
    MetricSummary,
)


def test_spans_overlap():
    # Overlapping spans
    assert spans_overlap(10, 20, 15, 25) is True
    assert spans_overlap(15, 25, 10, 20) is True
    assert spans_overlap(10, 30, 15, 20) is True  # Contained
    assert spans_overlap(15, 20, 10, 30) is True  # Enclosing

    # Disjoint spans
    assert spans_overlap(10, 20, 20, 30) is False  # Abutting
    assert spans_overlap(10, 20, 25, 35) is False
    assert spans_overlap(30, 40, 10, 20) is False


def test_finding_matches():
    exp = ExpectedFinding(
        entry_code="TERM-001",
        span_start=10,
        span_end=20,
        excerpt="serum",
        issue_type="terminology",
        verdict=None,
    )

    # 1. Exact match
    pred_exact = {
        "cited_entry_code": "TERM-001",
        "span_start": 10,
        "span_end": 20,
    }
    assert finding_matches(pred_exact, exp) is True

    # 2. Overlapping span match
    pred_overlap = {
        "cited_entry_code": "term-001",  # Case-insensitive
        "span_start": 12,
        "span_end": 18,
    }
    assert finding_matches(pred_overlap, exp) is True

    # 3. Disjoint span mismatch
    pred_disjoint = {
        "cited_entry_code": "TERM-001",
        "span_start": 25,
        "span_end": 35,
    }
    assert finding_matches(pred_disjoint, exp) is False

    # 4. Code mismatch despite overlapping span
    pred_diff_code = {
        "cited_entry_code": "TERM-002",
        "span_start": 10,
        "span_end": 20,
    }
    assert finding_matches(pred_diff_code, exp) is False

    # 5. Verdict matching
    claim_exp = ExpectedFinding(
        entry_code="FACT-001",
        span_start=0,
        span_end=15,
        excerpt="visible outcome",
        issue_type="claim",
        verdict="Supported",
    )
    pred_claim_match = {
        "cited_entry_code": "FACT-001",
        "span_start": 0,
        "span_end": 15,
        "claim_verdict": "Supported",
    }
    pred_claim_diff_verdict = {
        "cited_entry_code": "FACT-001",
        "span_start": 0,
        "span_end": 15,
        "claim_verdict": "Contradicted",
    }

    assert finding_matches(pred_claim_match, claim_exp, require_verdict_match=True) is True
    assert finding_matches(pred_claim_diff_verdict, claim_exp, require_verdict_match=True) is False
    assert finding_matches(pred_claim_diff_verdict, claim_exp, require_verdict_match=False) is True


def test_hand_computed_case_perfect_match():
    doc = EvalDocument(
        id="d-1",
        channel="social",
        title="Test",
        text="Sample text with serum and cure here.",
        expected_findings=[
            ExpectedFinding("TERM-001", 17, 22, "serum", "terminology"),
            ExpectedFinding("TERM-004", 27, 31, "cure", "terminology"),
        ],
    )
    preds = {
        "d-1": [
            {"cited_entry_code": "TERM-001", "span_start": 17, "span_end": 22, "issue_type": "terminology"},
            {"cited_entry_code": "TERM-004", "span_start": 27, "span_end": 31, "issue_type": "terminology"},
        ]
    }

    report = compute_eval_metrics([doc], preds)
    ov = report.overall

    assert ov.true_positives == 2
    assert ov.false_positives == 0
    assert ov.false_negatives == 0
    assert pytest.approx(ov.precision) == 1.0
    assert pytest.approx(ov.recall) == 1.0
    assert pytest.approx(ov.f1) == 1.0


def test_hand_computed_case_complete_miss():
    doc = EvalDocument(
        id="d-2",
        channel="social",
        title="Test",
        text="Sample text with serum and cure.",
        expected_findings=[
            ExpectedFinding("TERM-001", 17, 22, "serum", "terminology"),
            ExpectedFinding("TERM-004", 27, 31, "cure", "terminology"),
        ],
    )
    preds = {"d-2": []}

    report = compute_eval_metrics([doc], preds)
    ov = report.overall

    assert ov.true_positives == 0
    assert ov.false_positives == 0
    assert ov.false_negatives == 2
    assert ov.precision == 0.0
    assert ov.recall == 0.0
    assert ov.f1 == 0.0
    assert len(report.false_negatives) == 2


def test_hand_computed_case_clean_document_false_positive():
    clean_doc = EvalDocument(
        id="clean-1",
        channel="social",
        title="Clean Post",
        text="Completely clean compliant copy.",
        expected_findings=[],
    )
    preds = {
        "clean-1": [
            {
                "cited_entry_code": "TERM-001",
                "span_start": 0,
                "span_end": 10,
                "issue_type": "terminology",
                "excerpt": "Completely",
            }
        ]
    }

    report = compute_eval_metrics([clean_doc], preds)
    ov = report.overall

    assert report.clean_documents == 1
    assert report.clean_documents_passed == 0
    assert ov.true_positives == 0
    assert ov.false_positives == 1
    assert ov.false_negatives == 0
    assert ov.precision == 0.0
    assert ov.recall == 1.0
    assert ov.f1 == 0.0
    assert len(report.false_positives) == 1


def test_hand_computed_case_duplicate_predictions_on_same_expected():
    """If model emits two duplicate predictions matching the same single ground-truth finding, only 1 is TP, the second is FP."""
    doc = EvalDocument(
        id="d-3",
        channel="web",
        title="Dupe Test",
        text="Our serum is great.",
        expected_findings=[
            ExpectedFinding("TERM-001", 4, 9, "serum", "terminology")
        ],
    )
    preds = {
        "d-3": [
            {"cited_entry_code": "TERM-001", "span_start": 4, "span_end": 9, "issue_type": "terminology"},
            {"cited_entry_code": "TERM-001", "span_start": 4, "span_end": 9, "issue_type": "terminology"},
        ]
    }

    report = compute_eval_metrics([doc], preds)
    ov = report.overall

    assert ov.true_positives == 1
    assert ov.false_positives == 1
    assert ov.false_negatives == 0
    # Precision = 1 / (1 + 1) = 0.5; Recall = 1 / (1 + 0) = 1.0; F1 = 2 * (0.5 * 1.0) / 1.5 = 0.6667
    assert pytest.approx(ov.precision) == 0.5
    assert pytest.approx(ov.recall) == 1.0
    assert pytest.approx(ov.f1, rel=1e-3) == 0.6667
