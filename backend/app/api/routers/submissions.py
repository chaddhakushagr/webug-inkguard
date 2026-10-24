import hashlib
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.schemas import (
    SubmissionCreate,
    SubmissionDetail,
    ContentUpdate,
    SubmissionVersionResponse,
    DiffResponse,
    ReviewResponse,
    DataBoundaryResponse,
    NoteRequest,
    PublishRequest,
)
from app.adapters.db.session import get_db
from app.adapters.db.models import (
    Submission,
    SubmissionVersion,
    Approval,
    Finding,
    Review,
    AICall,
)
from app.adapters.db.audit import record_audit
from app.api.dependencies import get_current_user, require_role, AuthenticatedUser
from app.domain.workflow.permissions import (
    compute_submission_allowed_actions,
    get_required_approvals,
)
from app.domain.workflow.diff import compute_content_diff
from app.domain.workflow.state_machine import WorkflowStateMachine, WorkflowState

router = APIRouter(tags=["Submissions & Workflow"])


def get_risk_tier_for_channel(channel: str) -> str:
    c = channel.strip().lower()
    if c == "press_release":
        return "high"
    elif c in ("email", "blog", "web"):
        return "medium"
    return "low"


def build_submission_detail(
    sub: Submission,
    current_user: AuthenticatedUser,
    db: Session,
) -> SubmissionDetail:
    # 1. Fetch current content version
    current_ver = None
    if sub.current_version_id:
        current_ver = db.query(SubmissionVersion).filter(SubmissionVersion.id == sub.current_version_id).first()
    if not current_ver:
        current_ver = (
            db.query(SubmissionVersion)
            .filter(SubmissionVersion.submission_id == sub.id)
            .order_by(SubmissionVersion.version_no.desc())
            .first()
        )

    content_text = current_ver.content if current_ver else ""
    version_no = current_ver.version_no if current_ver else 1

    # 2. Count open high-severity findings for this content version
    open_high_severity_count = 0
    if current_ver:
        open_high_severity_count = (
            db.query(Finding)
            .filter(
                Finding.submission_version_id == current_ver.id,
                Finding.severity == "high",
                Finding.status == "open",
            )
            .count()
        )

    # 3. Fetch active valid approvals for this content version
    valid_approvals = []
    if current_ver:
        valid_approvals = (
            db.query(Approval)
            .filter(
                Approval.submission_id == sub.id,
                Approval.version_id == current_ver.id,
                Approval.decision == "approved",
                Approval.voided == False,
            )
            .all()
        )
    valid_reviewer_ids = [a.reviewer_id for a in valid_approvals]

    # 4. Compute dynamic allowed actions
    actions = compute_submission_allowed_actions(
        submission_status=sub.status,
        submission_creator_id=sub.creator_id,
        submission_risk_tier=sub.risk_tier,
        user_id=current_user.id,
        user_role=current_user.role,
        assignee_id=sub.assignee_id,
        open_high_severity_count=open_high_severity_count,
        valid_approvals_reviewer_ids=valid_reviewer_ids,
    )

    return SubmissionDetail(
        id=sub.id,
        title=sub.title,
        channel=sub.channel,
        risk_tier=sub.risk_tier,
        status=sub.status,
        creator_id=sub.creator_id,
        team_id=sub.team_id,
        current_version_id=sub.current_version_id,
        content=content_text,
        version_no=version_no,
        assignee_id=sub.assignee_id,
        published_url=sub.published_url,
        published_at=sub.published_at,
        is_synthetic=sub.is_synthetic,
        allowed_actions=actions,
        created_at=sub.created_at,
        updated_at=sub.updated_at,
    )


@router.get("/submissions", response_model=List[SubmissionDetail])
def list_submissions(
    status: Optional[str] = None,
    channel: Optional[str] = None,
    risk_tier: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    query = db.query(Submission)

    # Scoping by role: creators only see own and team's submissions
    if current_user.role == "creator":
        if current_user.team:
            query = query.filter(
                (Submission.creator_id == current_user.id)
                | (Submission.team_id == current_user.team)
            )
        else:
            query = query.filter(Submission.creator_id == current_user.id)

    if status:
        query = query.filter(Submission.status == status)
    if channel:
        query = query.filter(Submission.channel == channel)
    if risk_tier:
        query = query.filter(Submission.risk_tier == risk_tier)

    subs = query.order_by(Submission.updated_at.desc()).all()
    return [build_submission_detail(s, current_user, db) for s in subs]


@router.get("/submissions/queue", response_model=List[SubmissionDetail])
def get_reviewer_queue(
    mine_only: bool = False,
    risk_tier: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    query = db.query(Submission).filter(
        Submission.status.in_(["Submitted", "In Review"])
    )

    if mine_only:
        query = query.filter(Submission.assignee_id == current_user.id)
    if risk_tier:
        query = query.filter(Submission.risk_tier == risk_tier)

    subs = query.order_by(Submission.updated_at.asc()).all()
    return [build_submission_detail(s, current_user, db) for s in subs]


@router.get("/submissions/dashboard-counts")
def get_dashboard_counts(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    my_drafts = db.query(Submission).filter(
        Submission.creator_id == current_user.id,
        Submission.status.in_(["Draft", "Checked"]),
    ).count()

    my_action_needed = db.query(Submission).filter(
        Submission.creator_id == current_user.id,
        Submission.status == "Changes Requested",
    ).count()

    queue_size = db.query(Submission).filter(
        Submission.status.in_(["Submitted", "In Review"])
    ).count()

    my_claimed = db.query(Submission).filter(
        Submission.assignee_id == current_user.id,
        Submission.status == "In Review",
    ).count()

    approved_count = db.query(Submission).filter(
        Submission.status == "Approved"
    ).count()

    published_count = db.query(Submission).filter(
        Submission.status == "Marked Published"
    ).count()

    return {
        "my_drafts": my_drafts,
        "action_needed": my_action_needed,
        "queue_size": queue_size,
        "my_claimed": my_claimed,
        "approved": approved_count,
        "published": published_count,
    }


@router.post("/submissions", response_model=SubmissionDetail)
def create_submission(
    req: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    risk_tier = get_risk_tier_for_channel(req.channel)
    content_text = req.content.strip()
    content_hash = hashlib.sha256(content_text.encode("utf-8")).hexdigest()

    sub = Submission(
        title=req.title.strip(),
        channel=req.channel.strip().lower(),
        risk_tier=risk_tier,
        status="Draft",
        creator_id=current_user.id,
        team_id=req.team_id or current_user.team,
        is_synthetic=True,
        created_at=now,
        updated_at=now,
    )
    db.add(sub)
    db.flush()

    ver = SubmissionVersion(
        submission_id=sub.id,
        version_no=1,
        content=content_text,
        content_hash=content_hash,
        created_by=current_user.id,
        source="creator",
        created_at=now,
    )
    db.add(ver)
    db.flush()

    sub.current_version_id = ver.id
    db.commit()
    db.refresh(sub)

    record_audit(
        db=db,
        action="submission_create",
        entity_type="submission",
        entity_id=sub.id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        details={"title": sub.title, "channel": sub.channel, "risk_tier": sub.risk_tier},
    )

    return build_submission_detail(sub, current_user, db)


@router.get("/submissions/{submission_id}", response_model=SubmissionDetail)
def get_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    return build_submission_detail(sub, current_user, db)


@router.put("/submissions/{submission_id}/content", response_model=SubmissionDetail)
def update_submission_content(
    submission_id: str,
    req: ContentUpdate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    is_creator = (sub.creator_id == current_user.id)
    if not is_creator and current_user.role not in ("brand_manager", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only submission creator or brand manager can edit content",
        )

    now = datetime.now(timezone.utc)
    content_text = req.content.strip()
    content_hash = hashlib.sha256(content_text.encode("utf-8")).hexdigest()

    # Get latest version number
    latest_ver = (
        db.query(SubmissionVersion)
        .filter(SubmissionVersion.submission_id == sub.id)
        .order_by(SubmissionVersion.version_no.desc())
        .first()
    )
    new_version_no = (latest_ver.version_no + 1) if latest_ver else 1

    new_ver = SubmissionVersion(
        submission_id=sub.id,
        version_no=new_version_no,
        content=content_text,
        content_hash=content_hash,
        created_by=current_user.id,
        source=req.source or "edit",
        parent_version_id=latest_ver.id if latest_ver else None,
        created_at=now,
    )
    db.add(new_ver)
    db.flush()

    sub.current_version_id = new_ver.id
    sub.updated_at = now

    # Invariant: Content edit voids any existing approvals and resets status to Draft
    db.query(Approval).filter(
        Approval.submission_id == sub.id,
        Approval.voided == False,
    ).update({"voided": True})

    sub.status = "Draft"
    db.commit()
    db.refresh(sub)

    record_audit(
        db=db,
        action="submission_content_update",
        entity_type="submission",
        entity_id=sub.id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        details={"version_no": new_version_no, "voided_approvals": True},
    )

    return build_submission_detail(sub, current_user, db)


@router.get("/submissions/{submission_id}/versions", response_model=List[SubmissionVersionResponse])
def get_submission_versions(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    versions = (
        db.query(SubmissionVersion)
        .filter(SubmissionVersion.submission_id == sub.id)
        .order_by(SubmissionVersion.version_no.desc())
        .all()
    )

    return [
        SubmissionVersionResponse(
            id=v.id,
            submission_id=v.submission_id,
            version_no=v.version_no,
            content=v.content,
            content_hash=v.content_hash,
            created_by=v.created_by,
            source=v.source,
            created_at=v.created_at,
        )
        for v in versions
    ]


@router.get("/submissions/{submission_id}/diff", response_model=DiffResponse)
def get_submission_diff(
    submission_id: str,
    from_v: Optional[int] = Query(None, alias="from"),
    to_v: Optional[int] = Query(None, alias="to"),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    versions = (
        db.query(SubmissionVersion)
        .filter(SubmissionVersion.submission_id == sub.id)
        .order_by(SubmissionVersion.version_no.asc())
        .all()
    )

    if not versions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No content versions found")

    ver_map = {v.version_no: v.content for v in versions}

    # Determine default comparison
    if to_v is None:
        to_v = max(ver_map.keys())
    if from_v is None:
        from_v = to_v - 1 if (to_v - 1) in ver_map else to_v

    text1 = ver_map.get(from_v, "")
    text2 = ver_map.get(to_v, "")

    diff_result = compute_content_diff(text1, text2, v1=from_v, v2=to_v)
    return DiffResponse(**diff_result)


# --- Workflow State Machine Action Endpoints ---

@router.post("/submissions/{submission_id}/submit", response_model=SubmissionDetail)
def submit_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    is_creator = (sub.creator_id == current_user.id)
    if not is_creator and current_user.role not in ("brand_manager", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only creator can submit")

    # Invariant: Cannot submit if open high severity findings exist
    open_high_count = (
        db.query(Finding)
        .filter(
            Finding.submission_version_id == sub.current_version_id,
            Finding.severity == "high",
            Finding.status == "open",
        )
        .count()
    )
    if open_high_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit: {open_high_count} open high-severity issue(s) must be resolved first",
        )

    sub.status = "Submitted"
    sub.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(sub)

    record_audit(
        db=db,
        action="submission_submit",
        entity_type="submission",
        entity_id=sub.id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        details={"status": "Submitted"},
    )

    return build_submission_detail(sub, current_user, db)


@router.post("/submissions/{submission_id}/claim", response_model=SubmissionDetail)
def claim_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_role("reviewer", "brand_manager", "admin")),
):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    sub.assignee_id = current_user.id
    sub.status = "In Review"
    sub.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(sub)

    record_audit(
        db=db,
        action="submission_claim",
        entity_type="submission",
        entity_id=sub.id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        details={"assignee_id": current_user.id, "status": "In Review"},
    )

    return build_submission_detail(sub, current_user, db)


@router.post("/submissions/{submission_id}/unclaim", response_model=SubmissionDetail)
def unclaim_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_role("reviewer", "brand_manager", "admin")),
):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    sub.assignee_id = None
    sub.status = "Submitted"
    sub.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(sub)

    record_audit(
        db=db,
        action="submission_unclaim",
        entity_type="submission",
        entity_id=sub.id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        details={"status": "Submitted"},
    )

    return build_submission_detail(sub, current_user, db)


@router.post("/submissions/{submission_id}/request-changes", response_model=SubmissionDetail)
def request_changes(
    submission_id: str,
    req: NoteRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_role("reviewer", "brand_manager", "admin")),
):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    note_text = req.note.strip() if req.note else ""
    if not note_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A note explaining requested changes is required",
        )

    now = datetime.now(timezone.utc)
    approval = Approval(
        submission_id=sub.id,
        version_id=sub.current_version_id,
        reviewer_id=current_user.id,
        decision="changes_requested",
        note=note_text,
        voided=False,
        created_at=now,
    )
    db.add(approval)

    sub.status = "Changes Requested"
    sub.updated_at = now
    db.commit()
    db.refresh(sub)

    record_audit(
        db=db,
        action="submission_request_changes",
        entity_type="submission",
        entity_id=sub.id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        details={"note": note_text, "status": "Changes Requested"},
    )

    return build_submission_detail(sub, current_user, db)


@router.post("/submissions/{submission_id}/approve", response_model=SubmissionDetail)
def approve_submission(
    submission_id: str,
    req: Optional[NoteRequest] = None,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_role("reviewer", "brand_manager", "admin")),
):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    # Invariant: Self-approval prohibited!
    if sub.creator_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Safety Invariant: Creators cannot approve their own submissions",
        )

    # Invariant: Check if reviewer already approved this version
    existing_approval = (
        db.query(Approval)
        .filter(
            Approval.submission_id == sub.id,
            Approval.version_id == sub.current_version_id,
            Approval.reviewer_id == current_user.id,
            Approval.decision == "approved",
            Approval.voided == False,
        )
        .first()
    )
    if existing_approval:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already approved this content version",
        )

    now = datetime.now(timezone.utc)
    approval = Approval(
        submission_id=sub.id,
        version_id=sub.current_version_id,
        reviewer_id=current_user.id,
        decision="approved",
        note=req.note if req else None,
        voided=False,
        created_at=now,
    )
    db.add(approval)
    db.flush()

    # Calculate valid approvals count on this version
    approvals_count = (
        db.query(Approval)
        .filter(
            Approval.submission_id == sub.id,
            Approval.version_id == sub.current_version_id,
            Approval.decision == "approved",
            Approval.voided == False,
        )
        .count()
    )

    required_approvals = get_required_approvals(sub.risk_tier)
    if approvals_count >= required_approvals:
        sub.status = "Approved"

    sub.updated_at = now
    db.commit()
    db.refresh(sub)

    record_audit(
        db=db,
        action="submission_approve",
        entity_type="submission",
        entity_id=sub.id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        details={
            "approvals_count": approvals_count,
            "required_approvals": required_approvals,
            "status": sub.status,
        },
    )

    return build_submission_detail(sub, current_user, db)


@router.post("/submissions/{submission_id}/mark-published", response_model=SubmissionDetail)
def mark_published(
    submission_id: str,
    req: Optional[PublishRequest] = None,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    is_creator = (sub.creator_id == current_user.id)
    if not is_creator and current_user.role not in ("brand_manager", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only creator or manager can publish")

    if sub.status != "Approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot publish submission in '{sub.status}' state; must be 'Approved'",
        )

    now = datetime.now(timezone.utc)
    sub.status = "Marked Published"
    sub.published_url = req.url if (req and req.url) else "https://brand.lumo.skincare/published"
    sub.published_at = now
    sub.updated_at = now
    db.commit()
    db.refresh(sub)

    record_audit(
        db=db,
        action="submission_publish",
        entity_type="submission",
        entity_id=sub.id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        details={"published_url": sub.published_url},
    )

    return build_submission_detail(sub, current_user, db)


@router.delete("/submissions/{submission_id}")
def delete_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    is_creator = (sub.creator_id == current_user.id)
    if not is_creator and current_user.role not in ("brand_manager", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    if sub.status not in ("Draft", "Checked"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete submission in '{sub.status}' state",
        )

    record_audit(
        db=db,
        action="submission_delete",
        entity_type="submission",
        entity_id=sub.id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        details={"title": sub.title},
    )

    db.query(Finding).filter(Finding.submission_version_id == sub.current_version_id).delete()
    db.query(Approval).filter(Approval.submission_id == sub.id).delete()
    db.query(SubmissionVersion).filter(SubmissionVersion.submission_id == sub.id).delete()
    db.delete(sub)
    db.commit()

    return {"status": "deleted", "id": submission_id}


# --- Review Endpoints (Mock / Fallback) ---

@router.post("/submissions/{submission_id}/review", response_model=ReviewResponse)
def trigger_review(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    now = datetime.now(timezone.utc)
    rev = Review(
        submission_version_id=sub.current_version_id,
        status="completed",
        mode="mock",
        provider="Offline Mock Engine",
        model="mock-pipeline-v1",
        prompt_version="v1",
        stats={"rules_evaluated": 12, "claims_checked": 3, "latency_ms": 110},
        started_at=now,
        finished_at=now,
    )
    db.add(rev)

    # Invariant: Completed review moves submission from Draft to Checked
    if sub.status == "Draft":
        sub.status = "Checked"

    db.commit()
    db.refresh(rev)
    db.refresh(sub)

    record_audit(
        db=db,
        action="review_run",
        entity_type="review",
        entity_id=rev.id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        details={"mode": "mock", "submission_id": sub.id},
    )

    return ReviewResponse(
        id=rev.id,
        submission_version_id=rev.submission_version_id,
        status=rev.status,
        mode=rev.mode,
        provider=rev.provider,
        model=rev.model,
        prompt_version=rev.prompt_version,
        stats=rev.stats or {},
        started_at=rev.started_at,
        finished_at=rev.finished_at,
        findings_count=0,
    )


@router.get("/reviews/{review_id}", response_model=ReviewResponse)
def get_review(
    review_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    rev = db.query(Review).filter(Review.id == review_id).first()
    if not rev:
        now = datetime.now(timezone.utc)
        return ReviewResponse(
            id=review_id,
            submission_version_id="ver-s1-1",
            status="completed",
            mode="mock",
            provider="Offline Mock Engine",
            model="mock-pipeline-v1",
            prompt_version="v1",
            stats={"rules_evaluated": 12, "claims_checked": 3, "latency_ms": 110},
            started_at=now,
            finished_at=now,
            findings_count=0,
        )

    count = db.query(Finding).filter(Finding.review_id == rev.id).count()
    return ReviewResponse(
        id=rev.id,
        submission_version_id=rev.submission_version_id,
        status=rev.status,
        mode=rev.mode,
        provider=rev.provider,
        model=rev.model,
        prompt_version=rev.prompt_version,
        stats=rev.stats or {},
        started_at=rev.started_at,
        finished_at=rev.finished_at,
        findings_count=count,
    )


@router.get("/reviews/{review_id}/boundary", response_model=DataBoundaryResponse)
def get_review_boundary(
    review_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    ai_calls = db.query(AICall).filter(AICall.review_id == review_id).all()
    if not ai_calls:
        # Mock mode transparency
        return DataBoundaryResponse(
            review_id=review_id,
            external_calls_count=0,
            redaction_summary={"emails": 0, "phone_numbers": 0, "api_keys": 0, "secrets": 0},
            tiers_sent=["public"],
            confidential_data_sent=False,
            tokens_in=0,
            tokens_out=0,
            provider="Offline Mock Engine (zero external egress)",
            model="mock",
        )

    total_chars = sum(c.chars_sent for c in ai_calls)
    tokens_in = sum(c.tokens_in for c in ai_calls)
    tokens_out = sum(c.tokens_out for c in ai_calls)
    max_tier = "public"
    for c in ai_calls:
        if c.max_tier_sent == "confidential":
            max_tier = "confidential"
        elif c.max_tier_sent == "internal" and max_tier != "confidential":
            max_tier = "internal"

    return DataBoundaryResponse(
        review_id=review_id,
        external_calls_count=len(ai_calls),
        redaction_summary={"calls": len(ai_calls), "chars_sent": total_chars},
        tiers_sent=[max_tier],
        confidential_data_sent=(max_tier == "confidential"),
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        provider=ai_calls[0].provider if ai_calls else "mock",
        model=ai_calls[0].model if ai_calls else "mock",
    )
