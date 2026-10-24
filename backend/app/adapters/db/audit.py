import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import event
from app.adapters.db.models import AuditLog

GENESIS_HASH = "0" * 64


def calculate_audit_hash(
    prev_hash: str,
    ts: datetime,
    actor_id: Optional[str],
    action: str,
    entity_type: str,
    entity_id: str,
    details: Dict[str, Any],
) -> str:
    """Calculates cryptographically chained SHA-256 hash for audit immutability."""
    details_str = json.dumps(details, sort_keys=True, default=str)
    raw = f"{prev_hash}|{ts.isoformat()}|{actor_id or ''}|{action}|{entity_type}|{entity_id}|{details_str}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def record_audit(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: str,
    actor_id: Optional[str] = None,
    actor_role: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> AuditLog:
    """
    Appends an immutable, hash-chained record to the audit trail.
    """
    if details is None:
        details = {}

    last_record = db.query(AuditLog).order_by(AuditLog.ts.desc(), AuditLog.id.desc()).first()
    prev_hash = last_record.hash if last_record else GENESIS_HASH

    now = datetime.now(timezone.utc)
    entry_hash = calculate_audit_hash(
        prev_hash=prev_hash,
        ts=now,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )

    log_entry = AuditLog(
        ts=now,
        actor_id=actor_id,
        actor_role=actor_role,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        request_id=request_id,
        prev_hash=prev_hash,
        hash=entry_hash,
    )
    db.add(log_entry)
    db.commit()
    return log_entry


# --- Immutability Guards ---
@event.listens_for(AuditLog, "before_update")
def guard_audit_update(mapper, connection, target):
    raise RuntimeError("Security Invariant Violated: AuditLog is append-only and cannot be modified.")


@event.listens_for(AuditLog, "before_delete")
def guard_audit_delete(mapper, connection, target):
    raise RuntimeError("Security Invariant Violated: AuditLog is append-only and cannot be deleted.")
