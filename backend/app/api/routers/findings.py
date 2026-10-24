"""
Findings API Router.
Provides finding listing with allowed_actions, acceptance (creating new version and resetting to Draft),
dismissal with mandatory reason code/text (422 if missing), and escalation.
Every state change appends to the immutable audit trail.
"""

import hashlib
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from app.api.schemas import (
    FindingResponse,
    FindingDismissRequest,
    FindingEscalateRequest,
)
from app.adapters.db.session import get_db
from app.adapters.db.models import (
    Finding,
    FindingAction,
    Submission,
    SubmissionVersion,
    Approval,
    Comment,
)
from app.adapters.db.audit import record_audit
from app.api.dependencies import get_current_user, AuthenticatedUser
from app.domain.workflow.permissions import compute_finding_allowed_actions

router = APIRouter(tags=["Findings"])


def finding_to_response(
    f: Finding,
    sub_creator_id: str,
    current_user: AuthenticatedUser,
) -> FindingResponse:
    actions = compute_finding_allowed_actions(
        finding_status=f.status,
        submission_creator_id=sub_creator_id,
        user_id=current_user.id,
        user_role=current_user.role,
    )
    # If finding has no suggested fix, remove 'accept' action
    if not f.suggested_fix and "accept" in actions:
        actions = [a for a in actions if a != "accept"]

    return FindingResponse(
        id=f.id,
        review_id=f.review_id,
        submission_version_id=f.submission_version_id,
        fingerprint=f.fingerprint,
        source=f.source,
        issue_type=f.issue_type,
        severity=f.severity,
        confidence=f.confidence,
        span_start=f.span_start,
        span_end=f.span_end,
        excerpt=f.excerpt,
        cited_entry_id=f.cited_entry_id,
        cited_entry_code=f.cited_entry_id,
        cited_entry_version=f.cited_entry_version,
        claim_verdict=f.claim_verdict,
        is_policy=f.is_policy,
        needs_human_judgment=f.needs_human_judgment,
        explanation=f.explanation,
        suggested_fix=f.suggested_fix,
        status=f.status,
        is_synthetic=f.is_synthetic,
        created_at=f.created_at,
        allowed_actions=actions,
    )


@router.get("/submissions/{submission_id}/findings", response_model=List[FindingResponse])
def get_submission_findings(
    submission_id: str,
    version_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    target_version_id = version_id or sub.current_version_id
    if not target_version_id:
        return []

    findings = (
        db.query(Finding)
        .filter(Finding.submission_version_id == target_version_id)
        .order_by(Finding.span_start.asc())
        .all()
    )

    return [finding_to_response(f, sub.creator_id, current_user) for f in findings]


@router.post("/findings/{finding_id}/accept", response_model=FindingResponse)
def accept_finding(
    finding_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")

    sub_ver = db.query(SubmissionVersion).filter(SubmissionVersion.id == finding.submission_version_id).first()
    if not sub_ver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission version not found")

    sub = db.query(Submission).filter(Submission.id == sub_ver.submission_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    actions = compute_finding_allowed_actions(
        finding_status=finding.status,
        submission_creator_id=sub.creator_id,
        user_id=current_user.id,
        user_role=current_user.role,
    )
    if "accept" not in actions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to accept this finding",
        )

    if not finding.suggested_fix:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Finding has no suggested fix to accept",
        )

    # Conflict check: ensure finding is on the active version
    if sub.current_version_id != sub_ver.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Finding is from an older version; cannot accept without re-reviewing current draft",
        )

    current_content = sub_ver.content
    target_span = current_content[finding.span_start : finding.span_end]
    if target_span != finding.excerpt:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Content span has changed since review (expected '{finding.excerpt}', found '{target_span}'); cannot apply replacement.",
        )

    # Apply replacement and create new SubmissionVersion
    new_content = current_content[: finding.span_start] + finding.suggested_fix + current_content[finding.span_end :]
    new_version_no = sub_ver.version_no + 1
    content_hash = hashlib.sha256(new_content.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)

    new_ver = SubmissionVersion(
        submission_id=sub.id,
        version_no=new_version_no,
        content=new_content,
        content_hash=content_hash,
        created_by=current_user.id,
        source="fix_accept",
        parent_version_id=sub_ver.id,
        created_at=now,
    )
    db.add(new_ver)
    db.flush()

    sub.current_version_id = new_ver.id
    sub.updated_at = now

    # Invariant: Content edit voids approvals and resets status to Draft
    db.query(Approval).filter(
        Approval.submission_id == sub.id,
        Approval.voided == False,
    ).update({"voided": True})
    sub.status = "Draft"

    # Invariant: Older version findings become superseded; accepted finding marked accepted
    db.query(Finding).filter(
        Finding.submission_version_id == sub_ver.id,
        Finding.id != finding.id,
        Finding.status == "open",
    ).update({"status": "superseded"})

    finding.status = "accepted"

    # Record FindingAction
    action = FindingAction(
        finding_id=finding.id,
        actor_id=current_user.id,
        action="accept",
        reason_text=f"Applied replacement: '{finding.suggested_fix}'",
        created_at=now,
    )
    db.add(action)

    db.commit()
    db.refresh(finding)
    db.refresh(sub)

    # Record audit log
    record_audit(
        db=db,
        action="finding_accept",
        entity_type="finding",
        entity_id=finding.id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        details={
            "submission_id": sub.id,
            "version_no": new_version_no,
            "suggested_fix": finding.suggested_fix,
        },
    )

    return finding_to_response(finding, sub.creator_id, current_user)


@router.post("/findings/{finding_id}/dismiss", response_model=FindingResponse)
def dismiss_finding(
    finding_id: str,
    req: FindingDismissRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    if not req.reason_code or not req.reason_code.strip() or not req.reason_text or not req.reason_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Both reason_code and reason_text are required to dismiss a finding",
        )

    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")

    sub_ver = db.query(SubmissionVersion).filter(SubmissionVersion.id == finding.submission_version_id).first()
    if not sub_ver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission version not found")

    sub = db.query(Submission).filter(Submission.id == sub_ver.submission_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    actions = compute_finding_allowed_actions(
        finding_status=finding.status,
        submission_creator_id=sub.creator_id,
        user_id=current_user.id,
        user_role=current_user.role,
    )
    if "dismiss" not in actions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to dismiss this finding",
        )

    now = datetime.now(timezone.utc)
    finding.status = "dismissed"

    action = FindingAction(
        finding_id=finding.id,
        actor_id=current_user.id,
        action="dismiss",
        reason_code=req.reason_code.strip(),
        reason_text=req.reason_text.strip(),
        created_at=now,
    )
    db.add(action)
    db.commit()
    db.refresh(finding)

    record_audit(
        db=db,
        action="finding_dismiss",
        entity_type="finding",
        entity_id=finding.id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        details={
            "submission_id": sub.id,
            "reason_code": req.reason_code.strip(),
            "reason_text": req.reason_text.strip(),
        },
    )

    return finding_to_response(finding, sub.creator_id, current_user)


@router.post("/findings/{finding_id}/escalate", response_model=FindingResponse)
def escalate_finding(
    finding_id: str,
    req: Optional[FindingEscalateRequest] = None,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")

    sub_ver = db.query(SubmissionVersion).filter(SubmissionVersion.id == finding.submission_version_id).first()
    if not sub_ver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission version not found")

    sub = db.query(Submission).filter(Submission.id == sub_ver.submission_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    actions = compute_finding_allowed_actions(
        finding_status=finding.status,
        submission_creator_id=sub.creator_id,
        user_id=current_user.id,
        user_role=current_user.role,
    )
    if "escalate" not in actions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to escalate this finding",
        )

    now = datetime.now(timezone.utc)
    finding.status = "escalated"

    note_text = req.note if (req and req.note) else "Escalated for senior brand review."
    action = FindingAction(
        finding_id=finding.id,
        actor_id=current_user.id,
        action="escalate",
        reason_text=note_text,
        created_at=now,
    )
    db.add(action)

    # Post a threaded comment on the submission linking to the finding
    comment = Comment(
        submission_id=sub.id,
        finding_id=finding.id,
        author_id=current_user.id,
        body=f"[Escalation] {note_text} (Finding on '{finding.excerpt}')",
        created_at=now,
    )
    db.add(comment)

    db.commit()
    db.refresh(finding)

    record_audit(
        db=db,
        action="finding_escalate",
        entity_type="finding",
        entity_id=finding.id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        details={"submission_id": sub.id, "note": note_text},
    )

    return finding_to_response(finding, sub.creator_id, current_user)
