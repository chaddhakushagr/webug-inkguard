from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.api.schemas import (
    KBEntryResponse,
    KBEntryCreate,
    KBEntryUpdate,
    KBVersionResponse,
    BulkKBImportRequest,
)

router = APIRouter(prefix="/kb", tags=["Knowledge Base"])

now = datetime.now(timezone.utc)

MOCK_KB: List[KBEntryResponse] = [
    KBEntryResponse(
        id="kb-term-001",
        code="TERM-001",
        type="term",
        title="Approved Product Naming: Lumo Glow Concentrate",
        body="The primary hydration treatment must always be referred to as 'Lumo Glow Concentrate', never as a 'serum'.",
        data={
            "banned": "serum",
            "preferred": "Lumo Glow Concentrate",
            "match_type": "exact",
            "severity": "high",
            "reason": "Brand positioning standardizes formulation distinction",
            "exceptions": ["hair serum"],
        },
        classification="internal",
        status="active",
        current_version=1,
        created_at=now,
        updated_at=now,
    ),
    KBEntryResponse(
        id="kb-fact-001",
        code="FACT-001",
        type="fact",
        title="Clinical Trial L-12 Hydration Study",
        body="Clinical study L-12 demonstrated visible skin hydration improvement within 4 weeks across 94% of tested subjects.",
        data={
            "statement": "Visible skin hydration improvement in 4 weeks",
            "source": "Clinical Study L-12",
            "source_url": "https://internal.lumo.skincare/studies/L-12.pdf",
            "valid_from": "2024-01-01",
            "valid_until": "2026-12-31",
        },
        classification="internal",
        status="active",
        current_version=2,
        created_at=now,
        updated_at=now,
    ),
    KBEntryResponse(
        id="kb-fact-expired",
        code="FACT-002",
        type="fact",
        title="2023 Consumer Perception Panel",
        body="98% reported softer morning feel in 7 days (Panel CP-08, expired June 2025).",
        data={
            "statement": "98% reported softer morning feel in 7 days",
            "source": "Consumer Panel CP-08",
            "valid_from": "2023-01-01",
            "valid_until": "2025-06-30",
        },
        classification="internal",
        status="active",
        current_version=1,
        created_at=now,
        updated_at=now,
    ),
    KBEntryResponse(
        id="kb-rule-confidential",
        code="CONF-001",
        type="rule",
        title="Project Lumina Secret Launch Date",
        body="Next generation product line 'Project Lumina' launches November 15, 2026. Strictly confidential.",
        data={
            "rule_type": "confidential_term",
            "pattern": r"Project Lumina|November 15",
            "applies_to_channels": ["social", "email", "web", "blog", "press_release"],
            "severity": "high",
            "message": "Unreleased confidential launch date cannot appear in public channels",
        },
        classification="confidential",
        status="active",
        current_version=1,
        created_at=now,
        updated_at=now,
    ),
    KBEntryResponse(
        id="kb-tone-001",
        code="TONE-001",
        type="tone",
        title="Brand Tone: Plain-spoken & Grounded",
        body="Avoid pseudoscientific buzzwords, miraculous promises, and exaggerated absolutes.",
        data={
            "attribute": "Plain-spoken",
            "guidance": "State benefits plainly with clarity and precision.",
            "good_examples": ["Formulated with cold-pressed rosehip seed extract."],
            "bad_examples": ["A magical miracle elixir that erases all damage."],
        },
        classification="public",
        status="active",
        current_version=1,
        created_at=now,
        updated_at=now,
    ),
]


@router.get("/entries", response_model=List[KBEntryResponse])
def list_kb_entries(type: Optional[str] = None):
    if type:
        return [e for e in MOCK_KB if e.type == type]
    return MOCK_KB


@router.post("/entries", response_model=KBEntryResponse)
def create_kb_entry(req: KBEntryCreate):
    entry = KBEntryResponse(
        id=f"kb-{req.code.lower()}",
        code=req.code,
        type=req.type,
        title=req.title,
        body=req.body,
        data=req.data,
        classification=req.classification,
        status="active",
        current_version=1,
        created_at=now,
        updated_at=now,
    )
    return entry


@router.get("/entries/{entry_id}", response_model=KBEntryResponse)
def get_kb_entry(entry_id: str):
    for e in MOCK_KB:
        if e.id == entry_id or e.code == entry_id:
            return e
    return MOCK_KB[0]


@router.put("/entries/{entry_id}", response_model=KBEntryResponse)
def update_kb_entry(entry_id: str, req: KBEntryUpdate):
    for e in MOCK_KB:
        if e.id == entry_id or e.code == entry_id:
            return e
    return MOCK_KB[0]


@router.post("/entries/{entry_id}/retire", response_model=KBEntryResponse)
def retire_kb_entry(entry_id: str):
    for e in MOCK_KB:
        if e.id == entry_id or e.code == entry_id:
            return e
    return MOCK_KB[0]


@router.get("/entries/{entry_id}/versions", response_model=List[KBVersionResponse])
def get_kb_entry_versions(entry_id: str):
    return [
        KBVersionResponse(
            id=f"v2-{entry_id}",
            entry_id=entry_id,
            version=2,
            snapshot={"title": "Updated clinical study validation", "valid_until": "2026-12-31"},
            changed_by="u-manager",
            change_note="Extended validity following phase 2 re-test",
            created_at=now,
        ),
        KBVersionResponse(
            id=f"v1-{entry_id}",
            entry_id=entry_id,
            version=1,
            snapshot={"title": "Initial trial documentation"},
            changed_by="u-admin",
            change_note="Initial entry",
            created_at=now,
        ),
    ]


@router.post("/import/bulk")
def bulk_import_kb(req: BulkKBImportRequest):
    return {"status": "imported", "count": len(req.entries)}
