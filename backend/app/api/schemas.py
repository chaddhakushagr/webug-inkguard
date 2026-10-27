from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


# --- Error Envelope ---
class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


# --- System & Auth ---
class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.2.0"
    db: str = "healthy"
    ai_mode: str = "mock"


class SystemStatusResponse(BaseModel):
    version: str = "0.2.0"
    commit: str = "05fbbb2"
    ai_mode: str = "mock"
    ai_provider: str = "mock"
    health: str = "healthy"
    daily_quota_limit: int = 100
    daily_calls_made: int = 0
    uptime_seconds: int = 3600
    db_connected: bool = True


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class DemoUser(BaseModel):
    id: str
    name: str
    email: str
    role: str
    max_tier: str
    team: Optional[str] = None
    description: str


# --- Users & Teams ---
class TeamSchema(BaseModel):
    id: str
    name: str


class UserSchema(BaseModel):
    id: str
    email: str
    name: str
    role: str
    max_tier: str
    team_id: Optional[str] = None
    is_active: bool = True


class UserCreate(BaseModel):
    email: str
    name: str
    password: Optional[str] = "LumoDemo2026!"
    role: str
    max_tier: str = "internal"
    team_id: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    max_tier: Optional[str] = None
    team_id: Optional[str] = None
    is_active: Optional[bool] = None


# --- Knowledge Base ---
class KBEntryCreate(BaseModel):
    code: str
    type: str  # term, fact, tone, rule, asset
    title: str
    body: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    classification: str = "internal"


class KBEntryUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    classification: Optional[str] = None
    change_note: Optional[str] = None


class KBEntryResponse(BaseModel):
    id: str
    code: str
    type: str
    title: str
    body: Optional[str] = None
    data: Dict[str, Any]
    classification: str
    owner_id: Optional[str] = None
    status: str
    current_version: int
    created_at: datetime
    updated_at: datetime


class KBVersionResponse(BaseModel):
    id: str
    entry_id: str
    version: int
    snapshot: Dict[str, Any]
    changed_by: Optional[str] = None
    change_note: Optional[str] = None
    created_at: datetime


class BulkKBImportRequest(BaseModel):
    entries: List[KBEntryCreate]


# --- Submissions & Content ---
class SubmissionCreate(BaseModel):
    title: str
    channel: str  # social, email, blog, web, press_release
    content: str
    team_id: Optional[str] = None


class ContentUpdate(BaseModel):
    content: str
    source: str = "editor"


class SubmissionVersionResponse(BaseModel):
    id: str
    submission_id: str
    version_no: int
    content: str
    content_hash: str
    created_by: str
    source: str
    created_at: datetime


class DiffResponse(BaseModel):
    from_version: int
    to_version: int
    diff_text: str
    added_lines: int
    removed_lines: int


class SubmissionDetail(BaseModel):
    id: str
    title: str
    channel: str
    risk_tier: str
    status: str
    creator_id: str
    team_id: Optional[str] = None
    current_version_id: Optional[str] = None
    content: str
    version_no: int
    assignee_id: Optional[str] = None
    published_url: Optional[str] = None
    published_at: Optional[datetime] = None
    is_synthetic: bool = True
    allowed_actions: List[str]
    created_at: datetime
    updated_at: datetime


# --- Review & Boundary ---
class ReviewResponse(BaseModel):
    id: str
    submission_version_id: str
    status: str  # extracting, rule_checks, retrieving, analysing, finalising, completed, failed
    mode: str
    provider: str
    model: str
    prompt_version: str
    stats: Dict[str, Any] = {}
    error: Optional[str] = None
    fallback_reason: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
    findings_count: int = 0


class DataBoundaryResponse(BaseModel):
    review_id: str
    external_calls_count: int
    redaction_summary: Dict[str, int] = {}
    tiers_sent: List[str] = []
    confidential_data_sent: bool = False
    tokens_in: int = 0
    tokens_out: int = 0
    provider: str
    model: str
    purpose: str = "policy_and_claim_verification"
    entry_codes_included: List[str] = []
    characters_sent: int = 0
    highest_tier_sent: str = "public"
    cache_hit: bool = False
    message: Optional[str] = None


# --- Findings ---
class FindingResponse(BaseModel):
    id: str
    review_id: str
    submission_version_id: str
    fingerprint: str
    source: str  # rule, ai
    issue_type: str
    severity: str
    confidence: float
    span_start: int
    span_end: int
    excerpt: str
    cited_entry_id: Optional[str] = None
    cited_entry_code: Optional[str] = None
    cited_entry_version: Optional[int] = None
    claim_verdict: Optional[str] = None
    is_policy: bool
    needs_human_judgment: bool
    explanation: str
    suggested_fix: Optional[str] = None
    verifier_verdict: Optional[str] = None
    verifier_reason: Optional[str] = None
    status: str
    is_synthetic: bool
    created_at: datetime
    allowed_actions: List[str] = []


class FindingDismissRequest(BaseModel):
    reason_code: str
    reason_text: str


class FindingEscalateRequest(BaseModel):
    note: Optional[str] = None


# --- Workflow Actions ---
class NoteRequest(BaseModel):
    note: Optional[str] = None


class PublishRequest(BaseModel):
    url: Optional[str] = None


# --- Comments ---
class CommentCreate(BaseModel):
    body: str
    finding_id: Optional[str] = None
    parent_id: Optional[str] = None


class CommentResponse(BaseModel):
    id: str
    submission_id: str
    finding_id: Optional[str] = None
    parent_id: Optional[str] = None
    author_id: str
    author_name: str
    body: str
    created_at: datetime


# --- Insights ---
class InsightsSummary(BaseModel):
    total_reviews: int
    clean_submissions_pct: float
    avg_findings_per_review: float
    total_dismissals: int
    avg_review_turnaround_hours: float
    active_governance_rules: int
    synthetic_reviews_count: int = 0
    real_reviews_count: int = 0
    is_synthetic_included: bool = True


class RecurringIssue(BaseModel):
    issue_type: str
    rule_code: str
    rule_title: str
    count: int
    team_name: str
    week: str
    is_synthetic: bool = True


class DismissalBreakdown(BaseModel):
    reason_code: str
    count: int
    percentage: float


class RuleCounter(BaseModel):
    rule_code: str
    rule_title: str
    times_triggered: int
    times_dismissed: int
    times_accepted: int
    distinct_dismissers: int = 0


# --- Audit ---
class AuditLogResponse(BaseModel):
    id: str
    ts: datetime
    actor_id: Optional[str] = None
    actor_role: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    details: Dict[str, Any]
    request_id: Optional[str] = None
    prev_hash: Optional[str] = None
    hash: str
