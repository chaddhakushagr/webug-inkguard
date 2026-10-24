from datetime import datetime, timezone
from fastapi import APIRouter
from typing import List
from app.api.schemas import AuditLogResponse

router = APIRouter(tags=["Audit Log"])
now = datetime.now(timezone.utc)

MOCK_AUDIT: List[AuditLogResponse] = [
    AuditLogResponse(
        id="aud-003",
        ts=now,
        actor_id="u-creator-social",
        actor_role="creator",
        action="submission.created",
        entity_type="submission",
        entity_id="sub-sample-s1",
        details={"channel": "social", "risk_tier": "low", "title": "Spring Campaign Teaser Post"},
        request_id="req-9102-1234",
        prev_hash="a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0",
        hash="b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef01",
    ),
    AuditLogResponse(
        id="aud-002",
        ts=now,
        actor_id="u-creator-social",
        actor_role="creator",
        action="review.completed",
        entity_type="review",
        entity_id="rev-s1-active",
        details={"mode": "mock", "findings_count": 3, "rules_evaluated": 12},
        request_id="req-9102-1233",
        prev_hash="90123456789abcdef0123456789abcdef0123456789abcdef0123456789abcde",
        hash="a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0",
    ),
    AuditLogResponse(
        id="aud-001",
        ts=now,
        actor_id="u-admin",
        actor_role="admin",
        action="system.seed_initialized",
        entity_type="system",
        entity_id="sys-root",
        details={"seed_version": "1.0", "entries_count": 32},
        request_id="req-init-0001",
        prev_hash="0000000000000000000000000000000000000000000000000000000000000000",
        hash="90123456789abcdef0123456789abcdef0123456789abcdef0123456789abcde",
    ),
]


@router.get("/audit", response_model=List[AuditLogResponse])
def get_audit_log():
    return MOCK_AUDIT
