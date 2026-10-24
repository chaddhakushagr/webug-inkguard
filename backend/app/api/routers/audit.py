import io
import csv
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status, Query, Response
from typing import List, Optional
from sqlalchemy.orm import Session
from app.api.schemas import AuditLogResponse
from app.adapters.db.session import get_db
from app.adapters.db.models import AuditLog
from app.api.dependencies import get_current_user, require_role, AuthenticatedUser
from app.domain.workflow.permissions import can_view_audit, can_export_audit

router = APIRouter(tags=["Audit Log"])


def audit_to_response(a: AuditLog) -> AuditLogResponse:
    return AuditLogResponse(
        id=a.id,
        ts=a.ts,
        actor_id=a.actor_id,
        actor_role=a.actor_role,
        action=a.action,
        entity_type=a.entity_type,
        entity_id=a.entity_id,
        details=a.details or {},
        request_id=a.request_id,
        prev_hash=a.prev_hash,
        hash=a.hash,
    )


@router.get("/audit", response_model=List[AuditLogResponse])
def get_audit_log(
    actor_id: Optional[str] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    if not can_view_audit(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{current_user.role}' is not authorized to inspect system audit logs",
        )

    query = db.query(AuditLog)
    if actor_id:
        query = query.filter(AuditLog.actor_id == actor_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id)
    if from_date:
        query = query.filter(AuditLog.ts >= from_date)
    if to_date:
        query = query.filter(AuditLog.ts <= to_date)

    logs = query.order_by(AuditLog.ts.desc()).limit(limit).all()
    return [audit_to_response(a) for a in logs]


@router.get("/audit/export")
def export_audit_log_csv(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    if not can_export_audit(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{current_user.role}' is not authorized to export audit logs",
        )

    logs = db.query(AuditLog).order_by(AuditLog.ts.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id",
        "timestamp",
        "actor_id",
        "actor_role",
        "action",
        "entity_type",
        "entity_id",
        "details_json",
        "request_id",
        "prev_hash",
        "hash",
    ])

    for a in logs:
        writer.writerow([
            a.id,
            a.ts.isoformat() if a.ts else "",
            a.actor_id or "",
            a.actor_role or "",
            a.action,
            a.entity_type,
            a.entity_id,
            json.dumps(a.details, default=str),
            a.request_id or "",
            a.prev_hash or "",
            a.hash,
        ])

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=inkguard_audit_log.csv"},
    )
