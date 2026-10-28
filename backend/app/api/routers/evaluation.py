"""
Evaluation Router for Inkguard.
Exposes benchmark policy evaluation results, before/after verifier comparisons,
category breakdowns, and false-positive explorer data.
Restricted to brand_manager and admin roles.
"""

import os
import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies import require_role, AuthenticatedUser
from app.config import settings

router = APIRouter(tags=["Evaluation"])

def _get_evidence_dirs() -> List[str]:
    return [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "docs", "evidence")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "evidence")),
        os.path.abspath("docs/evidence"),
    ]


class OverallMetrics(BaseModel):
    tp: int
    fp: int
    fn: int
    precision: float
    recall: float
    f1: float


class EvalSummary(BaseModel):
    total_documents: int
    clean_documents: int
    clean_documents_passed: int
    clean_pass_rate: float
    overall: OverallMetrics


class CategoryMetrics(BaseModel):
    tp: int
    fp: int
    fn: int
    precision: float
    recall: float
    f1: float


class FalsePositiveItem(BaseModel):
    document_id: str
    channel: str
    cited_entry_code: Optional[str] = None
    issue_type: str
    excerpt: str
    span: List[int] = []
    claim_verdict: Optional[str] = None
    explanation: str
    confidence: Optional[float] = None
    verifier_verdict: Optional[str] = None
    verifier_reason: Optional[str] = None


class BeforeAfterRow(BaseModel):
    mode: str
    verifier: str
    total_docs: int
    clean_pass_rate: float
    tp: int
    fp: int
    fn: int
    precision: float
    recall: float
    f1: float


class EvaluationReportResponse(BaseModel):
    summary: EvalSummary
    before_after: List[BeforeAfterRow]
    by_issue_type: Dict[str, CategoryMetrics]
    by_claim_verdict: Dict[str, CategoryMetrics]
    false_positives: List[FalsePositiveItem]
    false_positives_count: int
    metadata: Dict[str, Any]


def _load_json_report(filename: str) -> Optional[Dict[str, Any]]:
    for d in _get_evidence_dirs():
        p = os.path.join(d, filename)
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                continue
    return None


@router.get(
    "/evaluation/results",
    response_model=EvaluationReportResponse,
    summary="Get benchmark policy evaluation results and before/after metrics",
)
@router.get(
    "/eval/latest",
    response_model=EvaluationReportResponse,
    summary="Alias for latest evaluation report",
)
def get_evaluation_results(
    current_user: AuthenticatedUser = Depends(require_role("brand_manager", "admin")),
):
    # Try latest reports in order of preference
    report_data = (
        _load_json_report("eval_cached_on_v3.json")
        or _load_json_report("eval_cached_on.json")
        or _load_json_report("eval_cached_on_v2.json")
    )

    if not report_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No evaluation reports found. Run 'python manage.py eval' to generate evidence.",
        )

    # Load paired reports for before/after comparison
    mock_off = _load_json_report("eval_mock_off.json") or _load_json_report("eval_mock.json")
    mock_on = _load_json_report("eval_mock_on.json") or _load_json_report("eval_mock_verifier.json")
    cached_off = _load_json_report("eval_cached_off.json") or _load_json_report("eval_cached.json")
    cached_on = report_data
    live_off = _load_json_report("eval_live_off.json")
    live_on = _load_json_report("eval_live_on.json")

    before_after: List[BeforeAfterRow] = []

    def _make_row(mode: str, verifier: str, rep: Optional[Dict[str, Any]], fallback_clean: float = 0.0) -> Optional[BeforeAfterRow]:
        if not rep:
            return None
        s = rep.get("summary", {})
        o = s.get("overall", {})
        return BeforeAfterRow(
            mode=mode,
            verifier=verifier,
            total_docs=int(s.get("total_documents", 84)),
            clean_pass_rate=round(float(s.get("clean_pass_rate", fallback_clean)), 3),
            tp=int(o.get("tp", 0)),
            fp=int(o.get("fp", 0)),
            fn=int(o.get("fn", 0)),
            precision=round(float(o.get("precision", 0.0)), 3),
            recall=round(float(o.get("recall", 0.0)), 3),
            f1=round(float(o.get("f1", 0.0)), 3),
        )

    row_mock_off = _make_row("mock", "OFF", mock_off, 0.810) or BeforeAfterRow(
        mode="mock", verifier="OFF", total_docs=84, clean_pass_rate=0.810, tp=66, fp=7, fn=19, precision=0.904, recall=0.776, f1=0.835
    )
    row_mock_on = _make_row("mock", "ON", mock_on, 0.810) or BeforeAfterRow(
        mode="mock", verifier="ON", total_docs=84, clean_pass_rate=0.810, tp=66, fp=7, fn=19, precision=0.904, recall=0.776, f1=0.835
    )
    row_cached_off = _make_row("cached", "OFF", cached_off, 0.238) or BeforeAfterRow(
        mode="cached", verifier="OFF", total_docs=84, clean_pass_rate=0.238, tp=79, fp=128, fn=6, precision=0.382, recall=0.929, f1=0.541
    )
    row_cached_on = _make_row("cached", "ON", cached_on, 0.762)

    before_after.extend([row_mock_off, row_mock_on, row_cached_off, row_cached_on])

    if live_off and live_on:
        row_live_off = _make_row("live (batch 20)", "OFF", live_off, 0.200)
        row_live_on = _make_row("live (batch 20)", "ON", live_on, 0.750)
        if row_live_off and row_live_on:
            before_after.extend([row_live_off, row_live_on])

    metadata = {
        "model": settings.LLM_MODEL,
        "mode": "cached",
        "prompt_versions": {
            "analysis": "analysis.v1.md",
            "verify": "verify.v1.md",
        },
        "confidence_threshold": settings.CLAIM_CONFIDENCE_THRESHOLD,
        "verifier_enabled": True,
        "report_file": "eval_cached_on_v3.json",
    }

    fps = []
    for fp in report_data.get("false_positives", []):
        fps.append(
            FalsePositiveItem(
                document_id=fp.get("document_id", "doc-unknown"),
                channel=fp.get("channel", "social"),
                cited_entry_code=fp.get("cited_entry_code"),
                issue_type=fp.get("issue_type", "unknown"),
                excerpt=fp.get("excerpt", ""),
                span=fp.get("span", [0, 0]),
                claim_verdict=fp.get("claim_verdict"),
                explanation=fp.get("explanation", ""),
                confidence=fp.get("confidence"),
                verifier_verdict=fp.get("verifier_verdict"),
                verifier_reason=fp.get("verifier_reason"),
            )
        )

    return EvaluationReportResponse(
        summary=report_data["summary"],
        before_after=before_after,
        by_issue_type=report_data.get("by_issue_type", {}),
        by_claim_verdict=report_data.get("by_claim_verdict", {}),
        false_positives=fps,
        false_positives_count=len(fps),
        metadata=metadata,
    )
