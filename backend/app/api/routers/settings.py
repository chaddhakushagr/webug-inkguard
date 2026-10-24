"""
Settings API Router.
Manages system settings: admin no_external_ai toggle, daily live LLM cap, thresholds, and egress policies.
Every update appends to the immutable audit log.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.adapters.db.session import get_db
from app.adapters.db.models import Setting
from app.adapters.db.audit import record_audit
from app.api.dependencies import get_current_user, require_role, AuthenticatedUser

router = APIRouter(tags=["Settings"])


@router.get("/settings", response_model=Dict[str, Any])
def get_settings(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    settings_records = db.query(Setting).all()
    result = {s.key: s.value for s in settings_records}
    # Ensure defaults
    if "no_external_ai" not in result:
        result["no_external_ai"] = False
    if "llm_daily_cap" not in result:
        result["llm_daily_cap"] = 100
    if "thresholds" not in result:
        result["thresholds"] = {"confidence": 0.6, "change_cap": 0.6, "max_chars": 20000}
    return result


@router.put("/settings", response_model=Dict[str, Any])
def update_settings(
    updates: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_role("admin", "brand_manager")),
):
    now = datetime.now(timezone.utc)
    for k, v in updates.items():
        s = db.query(Setting).filter(Setting.key == k).first()
        if not s:
            s = Setting(key=k, value=v, updated_at=now)
            db.add(s)
        else:
            s.value = v
            s.updated_at = now

    db.commit()

    record_audit(
        db=db,
        action="settings_update",
        entity_type="settings",
        entity_id="system_settings",
        actor_id=current_user.id,
        actor_role=current_user.role,
        details={"keys_updated": list(updates.keys())},
    )

    settings_records = db.query(Setting).all()
    return {s.key: s.value for s in settings_records}
