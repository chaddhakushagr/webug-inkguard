from datetime import datetime, timezone
from fastapi import APIRouter
from typing import List
from app.api.schemas import (
    FindingResponse,
    FindingDismissRequest,
    FindingEscalateRequest,
)

router = APIRouter(tags=["Findings"])
now = datetime.now(timezone.utc)

MOCK_FINDINGS: List[FindingResponse] = [
    FindingResponse(
        id="find-001",
        review_id="rev-s1-active",
        submission_version_id="ver-s1-1",
        fingerprint="fp-term-serum",
        source="rule",
        issue_type="terminology",
        severity="high",
        confidence=1.0,
        span_start=41,
        span_end=46,
        excerpt="serum",
        cited_entry_id="kb-term-001",
        cited_entry_code="TERM-001",
        cited_entry_version=1,
        claim_verdict=None,
        is_policy=True,
        needs_human_judgment=False,
        explanation="The product must be designated as 'Lumo Glow Concentrate', never as a 'serum'.",
        suggested_fix="Lumo Glow Concentrate",
        status="open",
        is_synthetic=True,
        created_at=now,
    ),
    FindingResponse(
        id="find-002",
        review_id="rev-s1-active",
        submission_version_id="ver-s1-1",
        fingerprint="fp-claim-cure",
        source="ai",
        issue_type="claim",
        severity="high",
        confidence=0.92,
        span_start=68,
        span_end=92,
        excerpt="completely cure dry skin",
        cited_entry_id="kb-fact-001",
        cited_entry_code="FACT-001",
        cited_entry_version=2,
        claim_verdict="Contradicted",
        is_policy=True,
        needs_human_judgment=False,
        explanation="Study L-12 supports 'visible skin hydration improvement', but explicitly refutes total cure claims.",
        suggested_fix="visibly improve dry skin",
        status="open",
        is_synthetic=True,
        created_at=now,
    ),
    FindingResponse(
        id="find-003",
        review_id="rev-s1-active",
        submission_version_id="ver-s1-1",
        fingerprint="fp-tone-miracle",
        source="rule",
        issue_type="tone",
        severity="medium",
        confidence=1.0,
        span_start=13,
        span_end=20,
        excerpt="miracle",
        cited_entry_id="kb-tone-001",
        cited_entry_code="TONE-001",
        cited_entry_version=1,
        claim_verdict=None,
        is_policy=True,
        needs_human_judgment=False,
        explanation="Brand tone guidelines prohibit hyperbolic superlatives and miracle claims.",
        suggested_fix="proven",
        status="open",
        is_synthetic=True,
        created_at=now,
    ),
]


@router.get("/submissions/{submission_id}/findings", response_model=List[FindingResponse])
def get_submission_findings(submission_id: str):
    return MOCK_FINDINGS


@router.post("/findings/{finding_id}/accept", response_model=FindingResponse)
def accept_finding(finding_id: str):
    for f in MOCK_FINDINGS:
        if f.id == finding_id:
            f.status = "accepted"
            return f
    return MOCK_FINDINGS[0]


@router.post("/findings/{finding_id}/dismiss", response_model=FindingResponse)
def dismiss_finding(finding_id: str, req: FindingDismissRequest):
    for f in MOCK_FINDINGS:
        if f.id == finding_id:
            f.status = "dismissed"
            return f
    return MOCK_FINDINGS[0]


@router.post("/findings/{finding_id}/escalate", response_model=FindingResponse)
def escalate_finding(finding_id: str, req: FindingEscalateRequest):
    for f in MOCK_FINDINGS:
        if f.id == finding_id:
            f.status = "escalated"
            return f
    return MOCK_FINDINGS[0]
