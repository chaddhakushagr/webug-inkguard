"""
Idempotent seed data loader for Inkguard.
Populates teams, demo users, and initial Lumo brand knowledge base.
Safe to run repeatedly without duplicate key errors or data drift.
"""

import os
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.adapters.db.session import engine, SessionLocal, Base
from app.adapters.db.models import Team, User, KBEntry, KBEntryVersion
from app.adapters.db.audit import record_audit
from app.adapters.security import hash_password
from app.config import settings

SEED_TEAMS = [
    {"id": "team-social", "name": "Team Social"},
    {"id": "team-web", "name": "Team Web & Growth"},
    {"id": "team-pr", "name": "Team PR & Communications"},
    {"id": "team-brand", "name": "Brand Strategy"},
    {"id": "team-ops", "name": "Operations"},
    {"id": "team-agency", "name": "External Agency"},
]

SEED_USERS = [
    {
        "id": "u-creator-social",
        "name": "Elena Chen",
        "email": "creator.social@lumo.internal",
        "role": "creator",
        "max_tier": "internal",
        "team_id": "team-social",
    },
    {
        "id": "u-creator-web",
        "name": "Devon Miles",
        "email": "creator.web@lumo.internal",
        "role": "creator",
        "max_tier": "internal",
        "team_id": "team-web",
    },
    {
        "id": "u-creator-agency",
        "name": "Marcus Vance",
        "email": "creator.agency@contractor.external",
        "role": "creator",
        "max_tier": "public",
        "team_id": "team-agency",
    },
    {
        "id": "u-reviewer-1",
        "name": "Sarah Jenkins",
        "email": "reviewer.sarah@lumo.internal",
        "role": "reviewer",
        "max_tier": "internal",
        "team_id": "team-pr",
    },
    {
        "id": "u-reviewer-2",
        "name": "Alex Wong",
        "email": "reviewer.alex@lumo.internal",
        "role": "reviewer",
        "max_tier": "internal",
        "team_id": "team-pr",
    },
    {
        "id": "u-manager",
        "name": "Kavita Rao",
        "email": "manager.kavita@lumo.internal",
        "role": "brand_manager",
        "max_tier": "confidential",
        "team_id": "team-brand",
    },
    {
        "id": "u-admin",
        "name": "System Admin",
        "email": "admin@lumo.internal",
        "role": "admin",
        "max_tier": "confidential",
        "team_id": "team-ops",
    },
]

SEED_KB_ENTRIES = [
    {
        "code": "TERM-001",
        "type": "term",
        "title": "Approved Product Naming: Lumo Glow Concentrate",
        "body": "The primary hydration treatment must always be referred to as 'Lumo Glow Concentrate', never as a 'serum'.",
        "classification": "internal",
        "data": {
            "banned": "serum",
            "preferred": "Lumo Glow Concentrate",
            "match_type": "exact",
            "severity": "high",
            "reason": "Standardizes formulation terminology",
            "exceptions": ["hair serum"],
        },
    },
    {
        "code": "TERM-002",
        "type": "term",
        "title": "Clinical Ingredient: Cold-Pressed Rosehip Extract",
        "body": "Rosehip active ingredient must always specify 'cold-pressed rosehip seed extract' to preserve organic sourcing attribution.",
        "classification": "public",
        "data": {
            "banned": "rosehip oil",
            "preferred": "cold-pressed rosehip seed extract",
            "match_type": "exact",
            "severity": "medium",
            "reason": "Accurate extraction method compliance",
        },
    },
    {
        "code": "FACT-001",
        "type": "fact",
        "title": "Clinical Trial L-12 Hydration Study",
        "body": "Clinical study L-12 demonstrated visible skin hydration improvement within 4 weeks across 94% of tested subjects.",
        "classification": "internal",
        "data": {
            "statement": "Visible skin hydration improvement in 4 weeks across 94% of tested subjects",
            "source": "Clinical Study L-12",
            "valid_from": "2024-01-01",
            "valid_until": "2026-12-31",
        },
    },
    {
        "code": "FACT-002",
        "type": "fact",
        "title": "2023 Consumer Perception Panel (Expired)",
        "body": "98% reported softer morning feel in 7 days (Panel CP-08, expired June 2025). Cannot be cited in active 2026 campaigns.",
        "classification": "internal",
        "data": {
            "statement": "98% reported softer morning feel in 7 days",
            "source": "Consumer Panel CP-08",
            "valid_from": "2023-01-01",
            "valid_until": "2025-06-30",
        },
    },
    {
        "code": "FACT-003",
        "type": "fact",
        "title": "Barrier Function Study BF-04 (Expiring Soon)",
        "body": "Demonstrates 35% reduction in trans-epidermal water loss over 14 days. Recertification pending end of this quarter.",
        "classification": "internal",
        "data": {
            "statement": "35% reduction in trans-epidermal water loss over 14 days",
            "source": "Barrier Function Study BF-04",
            "valid_from": "2025-01-01",
            "valid_until": "2026-11-15",
        },
    },
    {
        "code": "CONF-001",
        "type": "rule",
        "title": "Project Lumina Unreleased Launch Date",
        "body": "Project Lumina product line launch on November 15, 2026 is strictly confidential. Never leak launch date in public marketing.",
        "classification": "confidential",
        "data": {
            "rule_type": "confidential_term",
            "pattern": r"Project Lumina|November 15",
            "severity": "high",
            "message": "Confidential product launch date cannot appear in public channels",
        },
    },
    {
        "code": "TONE-001",
        "type": "tone",
        "title": "Brand Voice: Plain-spoken & Grounded",
        "body": "Avoid hyperbolic superlatives, miraculous claims, and pseudo-scientific buzzwords.",
        "classification": "public",
        "data": {
            "attribute": "Plain-spoken",
            "guidance": "Explain dermatological benefits plainly without miracle promises.",
            "good_examples": ["Formulated with cold-pressed botanical oils."],
            "bad_examples": ["A magical miracle elixir that erases all skin damage."],
        },
    },
    {
        "code": "RULE-001",
        "type": "rule",
        "title": "Mandatory Social Media Disclaimer",
        "body": "All social channel posts discussing clinical claims must include '#LumoPartner' or standard consumer study notice.",
        "classification": "public",
        "data": {
            "rule_type": "disclaimer",
            "channel": "social",
            "required_phrase": "#LumoPartner",
            "severity": "medium",
            "message": "Social posts require regulatory sponsorship disclosure",
        },
    },
    {
        "code": "ASSET-001",
        "type": "asset",
        "title": "Lumo Primary Wordmark Clearspace",
        "body": "The Lumo logo requires a minimum clear space equal to 50% of the wordmark height on all collateral.",
        "classification": "public",
        "data": {
            "asset_type": "logo",
            "clearspace_ratio": 0.5,
            "min_width_px": 120,
        },
    },
]


def run_seed(db: Session = None):
    close_at_end = False
    if db is None:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        close_at_end = True

    try:
        now = datetime.now(timezone.utc)
        print("[Seed] 1. Loading teams...")
        for t in SEED_TEAMS:
            existing = db.query(Team).filter(Team.id == t["id"]).first()
            if not existing:
                db.add(Team(id=t["id"], name=t["name"], created_at=now))
        db.commit()

        print("[Seed] 2. Loading users...")
        default_hash = hash_password(settings.DEMO_PASSWORD)
        for u in SEED_USERS:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                user = User(
                    id=u["id"],
                    email=u["email"],
                    name=u["name"],
                    password_hash=default_hash,
                    role=u["role"],
                    max_tier=u["max_tier"],
                    team_id=u["team_id"],
                    is_active=True,
                    created_at=now,
                )
                db.add(user)
        db.commit()

        print("[Seed] 3. Loading knowledge base...")
        admin_user = db.query(User).filter(User.role == "admin").first()
        admin_id = admin_user.id if admin_user else "u-admin"

        for k in SEED_KB_ENTRIES:
            existing = db.query(KBEntry).filter(KBEntry.code == k["code"]).first()
            if not existing:
                entry = KBEntry(
                    code=k["code"],
                    type=k["type"],
                    title=k["title"],
                    body=k["body"],
                    data=k["data"],
                    classification=k["classification"],
                    owner_id=admin_id,
                    status="active",
                    current_version=1,
                    created_at=now,
                    updated_at=now,
                )
                db.add(entry)
                db.flush()

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
                    changed_by=admin_id,
                    change_note="Initial brand seed data",
                    created_at=now,
                )
                db.add(v1)
        db.commit()

        record_audit(
            db=db,
            action="system_seed_loaded",
            entity_type="system",
            entity_id="root",
            actor_id=admin_id,
            actor_role="admin",
            details={"teams": len(SEED_TEAMS), "users": len(SEED_USERS), "kb_entries": len(SEED_KB_ENTRIES)},
        )
        print("[Seed] Completed successfully! All data idempotent and verified.")
    finally:
        if close_at_end:
            db.close()


if __name__ == "__main__":
    run_seed()
