from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
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

router = APIRouter(tags=["Submissions & Workflow"])
now = datetime.now(timezone.utc)

SAMPLE_CONTENT_S1 = (
    "Discover the miracle powers of our new age-smart serum! Clinically proven to completely cure dry skin "
    "and give you flawless radiance in just 2 days. Don't wait—our guaranteed #1 formula delivers 100% satisfaction."
)

MOCK_SUBMISSIONS: List[SubmissionDetail] = [
    SubmissionDetail(
        id="sub-sample-s1",
        title="Spring Campaign Teaser Post",
        channel="social",
        risk_tier="low",
        status="Checked",
        creator_id="u-creator-social",
        team_id="team-social",
        current_version_id="ver-s1-1",
        content=SAMPLE_CONTENT_S1,
        version_no=1,
        assignee_id="u-reviewer",
        published_url=None,
        published_at=None,
        is_synthetic=True,
        allowed_actions=["edit", "review", "submit", "comment"],
        created_at=now,
        updated_at=now,
    ),
    SubmissionDetail(
        id="sub-sample-s2",
        title="Lumo Glow Email Announcement",
        channel="email",
        risk_tier="medium",
        status="Submitted",
        creator_id="u-creator-web",
        team_id="team-web",
        current_version_id="ver-s2-1",
        content="Hey glow-getters! Experience the magic elixir that transforms your skin overnight.",
        version_no=1,
        assignee_id=None,
        published_url=None,
        published_at=None,
        is_synthetic=True,
        allowed_actions=["claim", "comment"],
        created_at=now,
        updated_at=now,
    ),
]


@router.get("/submissions", response_model=List[SubmissionDetail])
def list_submissions(status: Optional[str] = None):
    if status:
        return [s for s in MOCK_SUBMISSIONS if s.status == status]
    return MOCK_SUBMISSIONS


@router.post("/submissions", response_model=SubmissionDetail)
def create_submission(req: SubmissionCreate):
    sub = SubmissionDetail(
        id=f"sub-{datetime.now().strftime('%M%S')}",
        title=req.title,
        channel=req.channel,
        risk_tier="high" if req.channel == "press_release" else ("medium" if req.channel in ["email", "blog", "web"] else "low"),
        status="Draft",
        creator_id="u-creator-social",
        team_id=req.team_id or "team-social",
        current_version_id="ver-new-1",
        content=req.content,
        version_no=1,
        assignee_id=None,
        published_url=None,
        published_at=None,
        is_synthetic=True,
        allowed_actions=["edit", "review", "comment"],
        created_at=now,
        updated_at=now,
    )
    return sub


@router.get("/submissions/{submission_id}", response_model=SubmissionDetail)
def get_submission(submission_id: str):
    for s in MOCK_SUBMISSIONS:
        if s.id == submission_id:
            return s
    return MOCK_SUBMISSIONS[0]


@router.put("/submissions/{submission_id}/content", response_model=SubmissionDetail)
def update_submission_content(submission_id: str, req: ContentUpdate):
    for s in MOCK_SUBMISSIONS:
        if s.id == submission_id:
            s.content = req.content
            s.version_no += 1
            s.status = "Draft"
            s.allowed_actions = ["edit", "review", "comment"]
            return s
    return MOCK_SUBMISSIONS[0]


@router.get("/submissions/{submission_id}/versions", response_model=List[SubmissionVersionResponse])
def get_submission_versions(submission_id: str):
    return [
        SubmissionVersionResponse(
            id="ver-s1-1",
            submission_id=submission_id,
            version_no=1,
            content=SAMPLE_CONTENT_S1,
            content_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            created_by="u-creator-social",
            source="creator",
            created_at=now,
        )
    ]


@router.get("/submissions/{submission_id}/diff", response_model=DiffResponse)
def get_submission_diff(submission_id: str, from_v: int = Query(1, alias="from"), to_v: int = Query(2, alias="to")):
    return DiffResponse(
        from_version=from_v,
        to_version=to_v,
        diff_text="--- v1\n+++ v2\n- miracle powers of our new age-smart serum\n+ proven benefits of our new age-smart Lumo Glow Concentrate",
        added_lines=1,
        removed_lines=1,
    )


# --- Workflow Transitions ---
@router.post("/submissions/{submission_id}/submit", response_model=SubmissionDetail)
def submit_submission(submission_id: str):
    for s in MOCK_SUBMISSIONS:
        if s.id == submission_id:
            s.status = "Submitted"
            s.allowed_actions = ["claim", "comment"]
            return s
    return MOCK_SUBMISSIONS[0]


@router.post("/submissions/{submission_id}/claim", response_model=SubmissionDetail)
def claim_submission(submission_id: str):
    for s in MOCK_SUBMISSIONS:
        if s.id == submission_id:
            s.status = "In Review"
            s.assignee_id = "u-reviewer"
            s.allowed_actions = ["approve", "request-changes", "comment"]
            return s
    return MOCK_SUBMISSIONS[0]


@router.post("/submissions/{submission_id}/approve", response_model=SubmissionDetail)
def approve_submission(submission_id: str, req: Optional[NoteRequest] = None):
    for s in MOCK_SUBMISSIONS:
        if s.id == submission_id:
            s.status = "Approved"
            s.allowed_actions = ["mark-published", "comment"]
            return s
    return MOCK_SUBMISSIONS[0]


@router.post("/submissions/{submission_id}/request-changes", response_model=SubmissionDetail)
def request_changes(submission_id: str, req: NoteRequest):
    for s in MOCK_SUBMISSIONS:
        if s.id == submission_id:
            s.status = "Changes Requested"
            s.allowed_actions = ["edit", "comment"]
            return s
    return MOCK_SUBMISSIONS[0]


@router.post("/submissions/{submission_id}/mark-published", response_model=SubmissionDetail)
def mark_published(submission_id: str, req: Optional[PublishRequest] = None):
    for s in MOCK_SUBMISSIONS:
        if s.id == submission_id:
            s.status = "Marked Published"
            s.published_url = req.url if req else "https://instagram.com/p/mock-published"
            s.published_at = now
            s.allowed_actions = ["comment"]
            return s
    return MOCK_SUBMISSIONS[0]


# --- Review Endpoints ---
@router.post("/submissions/{submission_id}/review", response_model=ReviewResponse)
def trigger_review(submission_id: str):
    return ReviewResponse(
        id="rev-s1-active",
        submission_version_id="ver-s1-1",
        status="completed",
        mode="mock",
        provider="Offline Mock Engine",
        model="gemini-2.5-flash-mock",
        prompt_version="v1",
        stats={"rules_evaluated": 12, "claims_checked": 3, "latency_ms": 140},
        started_at=now,
        finished_at=now,
        findings_count=3,
    )


@router.get("/reviews/{review_id}", response_model=ReviewResponse)
def get_review(review_id: str):
    return ReviewResponse(
        id=review_id,
        submission_version_id="ver-s1-1",
        status="completed",
        mode="mock",
        provider="Offline Mock Engine",
        model="gemini-2.5-flash-mock",
        prompt_version="v1",
        stats={"rules_evaluated": 12, "claims_checked": 3, "latency_ms": 140},
        started_at=now,
        finished_at=now,
        findings_count=3,
    )


@router.get("/reviews/{review_id}/boundary", response_model=DataBoundaryResponse)
def get_review_boundary(review_id: str):
    return DataBoundaryResponse(
        review_id=review_id,
        external_calls_count=1,
        redaction_summary={"emails": 0, "phone_numbers": 0, "api_keys": 0, "sensitive_terms": 0},
        tiers_sent=["public", "internal"],
        confidential_data_sent=False,
        tokens_in=380,
        tokens_out=140,
        provider="Offline Mock Engine",
        model="gemini-2.5-flash-mock",
    )
