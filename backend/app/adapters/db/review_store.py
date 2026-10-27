"""
SQLAlchemy implementation of ReviewStorePort.
Owns database persistence for review lifecycle, findings, AI calls, and boundary records.
"""

import uuid
from datetime import datetime, timezone, date
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.ports.review_store import ReviewStorePort
from app.adapters.db.models import (
    Submission,
    SubmissionVersion,
    KBEntry,
    Review,
    Finding,
    AICall,
    Setting,
)
from app.adapters.db.audit import record_audit


class SqlAlchemyReviewStore(ReviewStorePort):
    """Database adapter implementing ReviewStorePort."""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    def get_submission_context(self, submission_id: str) -> Optional[Dict[str, Any]]:
        with self.session_factory() as db:
            sub = db.query(Submission).filter(Submission.id == submission_id).first()
            if not sub:
                return None

            ver = None
            if sub.current_version_id:
                ver = db.query(SubmissionVersion).filter(SubmissionVersion.id == sub.current_version_id).first()
            if not ver:
                ver = (
                    db.query(SubmissionVersion)
                    .filter(SubmissionVersion.submission_id == sub.id)
                    .order_by(SubmissionVersion.version_no.desc())
                    .first()
                )

            return {
                "id": sub.id,
                "title": sub.title,
                "channel": sub.channel,
                "risk_tier": sub.risk_tier,
                "status": sub.status,
                "creator_id": sub.creator_id,
                "team_id": sub.team_id,
                "current_version_id": ver.id if ver else None,
                "version_no": ver.version_no if ver else 1,
                "content": ver.content if ver else "",
            }

    def get_kb_pool(self, user_max_tier: str) -> List[Dict[str, Any]]:
        with self.session_factory() as db:
            entries = db.query(KBEntry).filter(KBEntry.status == "active").all()
            return [
                {
                    "id": e.id,
                    "code": e.code,
                    "type": e.type,
                    "title": e.title,
                    "body": e.body,
                    "data": e.data or {},
                    "classification": e.classification,
                    "current_version": e.current_version,
                }
                for e in entries
            ]

    def get_setting(self, key: str, default: Any = None) -> Any:
        with self.session_factory() as db:
            s = db.query(Setting).filter(Setting.key == key).first()
            if s and s.value is not None:
                return s.value
            return default

    def get_daily_live_calls_count(self) -> int:
        with self.session_factory() as db:
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            count = (
                db.query(AICall)
                .filter(
                    AICall.created_at >= today_start,
                    AICall.status == "success",
                    AICall.provider != "mock",
                    AICall.cache_hit == False,
                )
                .count()
            )
            return count

    def update_review_progress(self, review_id: str, status: str, error: Optional[str] = None) -> None:
        with self.session_factory() as db:
            rev = db.query(Review).filter(Review.id == review_id).first()
            if rev:
                rev.status = status
                if error:
                    rev.error = error
                db.commit()

    def save_review_results(
        self,
        review_id: str,
        submission_id: str,
        submission_version_id: str,
        findings: List[Dict[str, Any]],
        stats: Dict[str, Any],
        mode: str,
        provider: str,
        model: str,
        ai_call_data: Optional[Dict[str, Any]] = None,
        fallback_reason: Optional[str] = None,
        actor_id: Optional[str] = None,
        actor_role: Optional[str] = None,
    ) -> None:
        now = datetime.now(timezone.utc)
        with self.session_factory() as db:
            rev = db.query(Review).filter(Review.id == review_id).first()
            sub = db.query(Submission).filter(Submission.id == submission_id).first()

            # 1. Persist findings
            for item in findings:
                finding_id = str(uuid.uuid4())
                f = Finding(
                    id=finding_id,
                    review_id=review_id,
                    submission_version_id=submission_version_id,
                    fingerprint=item.get("fingerprint") or f"fp-{item.get('issue_type')}-{item.get('span_start')}",
                    source=item.get("source", "rule"),
                    issue_type=item.get("issue_type", "general_note"),
                    severity=item.get("severity", "medium"),
                    confidence=float(item.get("confidence", 1.0)),
                    span_start=int(item.get("span_start", 0)),
                    span_end=int(item.get("span_end", 0)),
                    excerpt=item.get("excerpt", ""),
                    cited_entry_id=item.get("cited_entry_id"),
                    cited_entry_version=item.get("cited_entry_version"),
                    claim_verdict=item.get("claim_verdict"),
                    is_policy=bool(item.get("is_policy", True)),
                    needs_human_judgment=bool(item.get("needs_human_judgment", False)),
                    explanation=item.get("explanation", ""),
                    suggested_fix=item.get("suggested_fix"),
                    verifier_verdict=item.get("verifier_verdict"),
                    verifier_reason=item.get("verifier_reason"),
                    status="open",
                    is_synthetic=True,
                    created_at=now,
                )
                db.add(f)

            # 2. Persist AI Call telemetry if present
            if ai_call_data:
                call_record = AICall(
                    review_id=review_id,
                    purpose=ai_call_data.get("purpose", "policy_and_claim_verification"),
                    provider=ai_call_data.get("provider", provider),
                    model=ai_call_data.get("model", model),
                    chars_sent=int(ai_call_data.get("chars_sent", 0)),
                    redaction_summary=ai_call_data.get("redaction_summary", {}),
                    kb_entry_ids=ai_call_data.get("kb_entry_ids", []),
                    max_tier_sent=ai_call_data.get("max_tier_sent", "public"),
                    status=ai_call_data.get("status", "success"),
                    latency_ms=int(ai_call_data.get("latency_ms", 0)),
                    tokens_in=int(ai_call_data.get("tokens_in", 0)),
                    tokens_out=int(ai_call_data.get("tokens_out", 0)),
                    cache_hit=bool(ai_call_data.get("cache_hit", False)),
                    created_at=now,
                )
                db.add(call_record)

            # 3. Update Review status and metadata
            if rev:
                rev.status = "completed"
                rev.mode = mode
                rev.provider = provider
                rev.model = model
                stats_dict = dict(stats or {})
                if fallback_reason:
                    stats_dict["fallback_reason"] = fallback_reason
                    rev.error = fallback_reason
                rev.stats = stats_dict
                rev.finished_at = now

            # 4. Transition Submission status to Checked if it was Draft
            if sub and sub.status in ("Draft", "new"):
                sub.status = "Checked"
                sub.updated_at = now

            db.commit()

            # 5. Append immutable cryptographic audit row
            record_audit(
                db=db,
                action="review_run",
                entity_type="review",
                entity_id=review_id,
                actor_id=actor_id,
                actor_role=actor_role or "system",
                details={
                    "mode": mode,
                    "submission_id": submission_id,
                    "findings_count": len(findings),
                    "fallback_reason": fallback_reason,
                },
            )

    def fail_review(self, review_id: str, error: str) -> None:
        now = datetime.now(timezone.utc)
        with self.session_factory() as db:
            rev = db.query(Review).filter(Review.id == review_id).first()
            if rev:
                rev.status = "failed"
                rev.error = error
                rev.finished_at = now
                db.commit()
