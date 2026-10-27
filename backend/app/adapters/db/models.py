import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    Float,
    DateTime,
    JSON,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from app.adapters.db.session import Base


def get_uuid() -> str:
    return str(uuid.uuid4())


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Team(Base):
    __tablename__ = "teams"

    id = Column(String(36), primary_key=True, default=get_uuid)
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=get_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # creator, reviewer, brand_manager, admin
    max_tier = Column(String(50), nullable=False, default="internal")  # public, internal, confidential
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    team = relationship("Team")


class KBEntry(Base):
    __tablename__ = "kb_entries"

    id = Column(String(36), primary_key=True, default=get_uuid)
    code = Column(String(50), unique=True, index=True, nullable=False)  # e.g. FACT-003
    type = Column(String(50), nullable=False)  # term, fact, tone, rule, asset
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=True)
    data = Column(JSON, default=dict)  # type-specific schema
    classification = Column(String(50), nullable=False, default="internal")  # public, internal, confidential
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    status = Column(String(50), default="active")  # active, retired
    current_version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    owner = relationship("User")


class KBEntryVersion(Base):
    __tablename__ = "kb_entry_versions"

    id = Column(String(36), primary_key=True, default=get_uuid)
    entry_id = Column(String(36), ForeignKey("kb_entries.id"), index=True, nullable=False)
    version = Column(Integer, nullable=False)
    snapshot = Column(JSON, nullable=False)
    changed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    change_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(String(36), primary_key=True, default=get_uuid)
    title = Column(String(255), nullable=False)
    channel = Column(String(50), nullable=False)  # social, email, blog, web, press_release
    risk_tier = Column(String(50), nullable=False)  # low, medium, high
    status = Column(String(50), nullable=False, default="Draft")  # Draft, Checked, Submitted, In Review, Changes Requested, Approved, Marked Published
    creator_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=True)
    current_version_id = Column(String(36), nullable=True)
    assignee_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    published_url = Column(String(500), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    is_synthetic = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    creator = relationship("User", foreign_keys=[creator_id])
    assignee = relationship("User", foreign_keys=[assignee_id])
    team = relationship("Team")


class SubmissionVersion(Base):
    __tablename__ = "submission_versions"

    id = Column(String(36), primary_key=True, default=get_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.id"), index=True, nullable=False)
    version_no = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    source = Column(String(50), default="creator")  # creator, fix_accept, edit
    parent_version_id = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)


class Review(Base):
    __tablename__ = "reviews"

    id = Column(String(36), primary_key=True, default=get_uuid)
    submission_version_id = Column(String(36), ForeignKey("submission_versions.id"), index=True, nullable=False)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    mode = Column(String(50), default="mock")  # live, cached, mock, rules_only
    provider = Column(String(50), default="mock")
    model = Column(String(100), default="mock")
    prompt_version = Column(String(50), default="v1")
    kb_snapshot = Column(JSON, default=list)
    kb_snapshot_hash = Column(String(64), nullable=True)
    redaction_log = Column(JSON, default=list)
    stats = Column(JSON, default=dict)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), default=get_utc_now)
    finished_at = Column(DateTime(timezone=True), nullable=True)


class Finding(Base):
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=get_uuid)
    review_id = Column(String(36), ForeignKey("reviews.id"), index=True, nullable=False)
    submission_version_id = Column(String(36), ForeignKey("submission_versions.id"), index=True, nullable=False)
    fingerprint = Column(String(64), index=True, nullable=False)
    source = Column(String(50), nullable=False)  # rule, ai
    issue_type = Column(String(50), nullable=False)  # terminology, tone, claim, missing_disclaimer, confidential_leak, accessibility, readability, general_note
    severity = Column(String(50), nullable=False)  # low, medium, high
    confidence = Column(Float, default=1.0)
    span_start = Column(Integer, nullable=False)
    span_end = Column(Integer, nullable=False)
    excerpt = Column(Text, nullable=False)
    cited_entry_id = Column(String(36), nullable=True)
    cited_entry_version = Column(Integer, nullable=True)
    claim_verdict = Column(String(50), nullable=True)  # Supported, Contradicted, Unverified, Expired
    is_policy = Column(Boolean, default=True)
    needs_human_judgment = Column(Boolean, default=False)
    explanation = Column(Text, nullable=False)
    suggested_fix = Column(Text, nullable=True)
    verifier_verdict = Column(String(32), nullable=True)
    verifier_reason = Column(Text, nullable=True)
    status = Column(String(50), default="open")  # open, accepted, dismissed, escalated
    is_synthetic = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)


class FindingAction(Base):
    __tablename__ = "finding_actions"

    id = Column(String(36), primary_key=True, default=get_uuid)
    finding_id = Column(String(36), ForeignKey("findings.id"), index=True, nullable=False)
    actor_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)  # accept, dismiss, escalate
    reason_code = Column(String(100), nullable=True)
    reason_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)


class Comment(Base):
    __tablename__ = "comments"

    id = Column(String(36), primary_key=True, default=get_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.id"), index=True, nullable=False)
    finding_id = Column(String(36), ForeignKey("findings.id"), nullable=True)
    parent_id = Column(String(36), ForeignKey("comments.id"), nullable=True)
    author_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    author = relationship("User")


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(String(36), primary_key=True, default=get_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.id"), index=True, nullable=False)
    version_id = Column(String(36), ForeignKey("submission_versions.id"), nullable=False)
    reviewer_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    decision = Column(String(50), nullable=False)  # approved, changes_requested
    note = Column(Text, nullable=True)
    voided = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    reviewer = relationship("User")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String(36), primary_key=True, default=get_uuid)
    ts = Column(DateTime(timezone=True), default=get_utc_now, index=True)
    actor_id = Column(String(36), nullable=True)
    actor_role = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=False)
    details = Column(JSON, default=dict)
    request_id = Column(String(64), nullable=True)
    prev_hash = Column(String(64), nullable=True)
    hash = Column(String(64), nullable=False)


class AICall(Base):
    __tablename__ = "ai_calls"

    id = Column(String(36), primary_key=True, default=get_uuid)
    review_id = Column(String(36), ForeignKey("reviews.id"), index=True, nullable=True)
    purpose = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    chars_sent = Column(Integer, default=0)
    redaction_summary = Column(JSON, default=dict)
    kb_entry_ids = Column(JSON, default=list)
    max_tier_sent = Column(String(50), default="internal")
    status = Column(String(50), default="success")
    latency_ms = Column(Integer, default=0)
    tokens_in = Column(Integer, default=0)
    tokens_out = Column(Integer, default=0)
    cache_hit = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)


class LLMCache(Base):
    __tablename__ = "llm_cache"

    key = Column(String(64), primary_key=True)
    response = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)


class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(100), primary_key=True)
    value = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)
