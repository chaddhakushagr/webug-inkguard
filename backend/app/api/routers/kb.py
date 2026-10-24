from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from app.api.schemas import (
    KBEntryResponse,
    KBEntryCreate,
    KBEntryUpdate,
    KBVersionResponse,
    BulkKBImportRequest,
)
from app.adapters.db.session import get_db
from app.adapters.db.models import KBEntry, KBEntryVersion
from app.adapters.db.audit import record_audit
from app.api.dependencies import get_current_user, require_role, AuthenticatedUser
from app.domain.workflow.permissions import can_access_tier, can_manage_kb, TIER_RANKS
from app.domain.kb.validity import check_fact_validity

router = APIRouter(prefix="/kb", tags=["Knowledge Base"])


def entry_to_response(e: KBEntry) -> KBEntryResponse:
    return KBEntryResponse(
        id=e.id,
        code=e.code,
        type=e.type,
        title=e.title,
        body=e.body,
        data=e.data or {},
        classification=e.classification,
        owner_id=e.owner_id,
        status=e.status,
        current_version=e.current_version,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )


@router.get("/entries", response_model=List[KBEntryResponse])
def list_kb_entries(
    type: Optional[str] = None,
    classification: Optional[str] = None,
    status: Optional[str] = "active",
    expiring_soon_only: bool = False,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    query = db.query(KBEntry)
    if status:
        query = query.filter(KBEntry.status == status)
    if type:
        query = query.filter(KBEntry.type == type)
    if classification:
        query = query.filter(KBEntry.classification == classification)

    entries = query.order_by(KBEntry.code.asc()).all()

    # Invariant: Tier filtering - entries above the user's tier NEVER appear
    accessible_entries = [
        e for e in entries if can_access_tier(current_user.max_tier, e.classification)
    ]

    if expiring_soon_only:
        filtered = []
        for e in accessible_entries:
            if e.type == "fact":
                val = check_fact_validity(e.data or {})
                if val.get("is_expiring_soon") or val.get("is_expired"):
                    filtered.append(e)
        accessible_entries = filtered

    return [entry_to_response(e) for e in accessible_entries]


@router.post("/entries", response_model=KBEntryResponse)
def create_kb_entry(
    req: KBEntryCreate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_role("brand_manager", "admin")),
):
    if req.classification not in TIER_RANKS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid classification '{req.classification}'. Valid: {list(TIER_RANKS.keys())}",
        )
    if req.type not in ("term", "fact", "tone", "rule", "asset"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid entry type '{req.type}'",
        )

    code_clean = req.code.strip().upper()
    existing = db.query(KBEntry).filter(KBEntry.code == code_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"KB entry with code '{code_clean}' already exists",
        )

    now = datetime.now(timezone.utc)
    entry = KBEntry(
        code=code_clean,
        type=req.type,
        title=req.title.strip(),
        body=req.body,
        data=req.data or {},
        classification=req.classification,
        owner_id=current_user.id,
        status="active",
        current_version=1,
        created_at=now,
        updated_at=now,
    )
    db.add(entry)
    db.flush()

    # Create immutable initial version
    v1 = KBEntryVersion(
        entry_id=entry.id,
        version=1,
        snapshot={
            "code": entry.code,
            "type": entry.type,
            "title": entry.title,
            "body": entry.body,
            "data": entry.data,
            "classification": entry.classification,
        },
        changed_by=current_user.id,
        change_note="Initial entry creation",
        created_at=now,
    )
    db.add(v1)
    db.commit()
    db.refresh(entry)

    record_audit(
        db=db,
        action="kb_create",
        entity_type="kb_entry",
        entity_id=entry.id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        details={"code": entry.code, "type": entry.type, "version": 1},
    )

    return entry_to_response(entry)


@router.get("/entries/{entry_id}", response_model=KBEntryResponse)
def get_kb_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    entry = db.query(KBEntry).filter(
        (KBEntry.id == entry_id) | (KBEntry.code == entry_id.upper())
    ).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KB entry not found")

    # Invariant: Tier clearance check
    if not can_access_tier(current_user.max_tier, entry.classification):
        # Entry above user's tier never appears
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KB entry not found")

    return entry_to_response(entry)


@router.put("/entries/{entry_id}", response_model=KBEntryResponse)
def update_kb_entry(
    entry_id: str,
    req: KBEntryUpdate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_role("brand_manager", "admin")),
):
    entry = db.query(KBEntry).filter(
        (KBEntry.id == entry_id) | (KBEntry.code == entry_id.upper())
    ).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KB entry not found")

    if not can_access_tier(current_user.max_tier, entry.classification):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient clearance")

    # Immutable version update: increment version and append to versions table
    new_version_no = entry.current_version + 1
    now = datetime.now(timezone.utc)

    if req.title is not None:
        entry.title = req.title.strip()
    if req.body is not None:
        entry.body = req.body
    if req.data is not None:
        entry.data = req.data
    if req.classification is not None:
        if req.classification not in TIER_RANKS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid classification")
        entry.classification = req.classification

    entry.current_version = new_version_no
    entry.updated_at = now

    new_version = KBEntryVersion(
        entry_id=entry.id,
        version=new_version_no,
        snapshot={
            "code": entry.code,
            "type": entry.type,
            "title": entry.title,
            "body": entry.body,
            "data": entry.data,
            "classification": entry.classification,
        },
        changed_by=current_user.id,
        change_note=req.change_note or f"Updated to version {new_version_no}",
        created_at=now,
    )
    db.add(new_version)
    db.commit()
    db.refresh(entry)

    record_audit(
        db=db,
        action="kb_update",
        entity_type="kb_entry",
        entity_id=entry.id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        details={"code": entry.code, "version": new_version_no, "note": req.change_note},
    )

    return entry_to_response(entry)


@router.post("/entries/{entry_id}/retire", response_model=KBEntryResponse)
def retire_kb_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_role("brand_manager", "admin")),
):
    entry = db.query(KBEntry).filter(
        (KBEntry.id == entry_id) | (KBEntry.code == entry_id.upper())
    ).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KB entry not found")

    entry.status = "retired"
    entry.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(entry)

    record_audit(
        db=db,
        action="kb_retire",
        entity_type="kb_entry",
        entity_id=entry.id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        details={"code": entry.code},
    )

    return entry_to_response(entry)


@router.get("/entries/{entry_id}/versions", response_model=List[KBVersionResponse])
def get_kb_entry_versions(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    entry = db.query(KBEntry).filter(
        (KBEntry.id == entry_id) | (KBEntry.code == entry_id.upper())
    ).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KB entry not found")

    if not can_access_tier(current_user.max_tier, entry.classification):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KB entry not found")

    versions = db.query(KBEntryVersion).filter(
        KBEntryVersion.entry_id == entry.id
    ).order_by(KBEntryVersion.version.desc()).all()

    return [
        KBVersionResponse(
            id=v.id,
            entry_id=v.entry_id,
            version=v.version,
            snapshot=v.snapshot,
            changed_by=v.changed_by,
            change_note=v.change_note,
            created_at=v.created_at,
        )
        for v in versions
    ]


@router.post("/import/bulk")
def bulk_import_kb(
    req: BulkKBImportRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_role("brand_manager", "admin")),
):
    imported_count = 0
    now = datetime.now(timezone.utc)

    for item in req.entries:
        code_clean = item.code.strip().upper()
        existing = db.query(KBEntry).filter(KBEntry.code == code_clean).first()
        if existing:
            # Update to new version
            existing.title = item.title.strip()
            existing.body = item.body
            existing.data = item.data or {}
            existing.classification = item.classification
            existing.current_version += 1
            existing.updated_at = now

            v = KBEntryVersion(
                entry_id=existing.id,
                version=existing.current_version,
                snapshot={
                    "code": existing.code,
                    "type": existing.type,
                    "title": existing.title,
                    "body": existing.body,
                    "data": existing.data,
                    "classification": existing.classification,
                },
                changed_by=current_user.id,
                change_note="Bulk import revision",
                created_at=now,
            )
            db.add(v)
        else:
            # Create new
            entry = KBEntry(
                code=code_clean,
                type=item.type,
                title=item.title.strip(),
                body=item.body,
                data=item.data or {},
                classification=item.classification,
                owner_id=current_user.id,
                status="active",
                current_version=1,
                created_at=now,
                updated_at=now,
            )
            db.add(entry)
            db.flush()

            v = KBEntryVersion(
                entry_id=entry.id,
                version=1,
                snapshot={
                    "code": entry.code,
                    "type": entry.type,
                    "title": entry.title,
                    "body": entry.body,
                    "data": entry.data,
                    "classification": entry.classification,
                },
                changed_by=current_user.id,
                change_note="Bulk import creation",
                created_at=now,
            )
            db.add(v)
        imported_count += 1

    db.commit()

    record_audit(
        db=db,
        action="kb_bulk_import",
        entity_type="kb_entry",
        entity_id="bulk",
        actor_id=current_user.id,
        actor_role=current_user.role,
        details={"count": imported_count},
    )

    return {"status": "imported", "count": imported_count}
