"""
Idempotent seed data loader for Inkguard.
Populates teams, demo users, initial Lumo brand knowledge base, and sample submissions S1-S5.
Safe to run repeatedly without duplicate key errors or data drift.
"""

import hashlib
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.adapters.db.session import engine, SessionLocal, Base
from app.adapters.db.models import (
    Team,
    User,
    KBEntry,
    KBEntryVersion,
    Submission,
    SubmissionVersion,
)
from app.adapters.db.audit import record_audit
from app.adapters.security import hash_password
from app.config import settings
from app.seed.lumo_brand import (
    SEED_TONE,
    SEED_TERMS,
    SEED_RULES,
    SEED_FACTS,
    SEED_ASSETS,
    SEED_SAMPLES,
)

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
        "id": "u-creator-maya",
        "name": "Maya Patel",
        "email": "creator.maya@lumo.internal",
        "role": "creator",
        "max_tier": "internal",
        "team_id": "team-social",
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

        print("[Seed] 2. Loading users (8 demo personas)...")
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

        print("[Seed] 3. Loading Lumo brand knowledge base (~45 curated entries)...")
        admin_user = db.query(User).filter(User.role == "admin").first()
        admin_id = admin_user.id if admin_user else "u-admin"

        all_kb_entries = (
            SEED_TONE + SEED_TERMS + SEED_RULES + SEED_FACTS + SEED_ASSETS
        )

        for k in all_kb_entries:
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

        print("[Seed] 4. Loading sample submissions (S1 to S5)...")
        creator_user = db.query(User).filter(User.role == "creator").first()
        creator_id = creator_user.id if creator_user else "u-creator-social"

        for s in SEED_SAMPLES:
            existing_sub = db.query(Submission).filter(Submission.id == s["id"]).first()
            if not existing_sub:
                content_text = s["content"].strip()
                content_hash = hashlib.sha256(content_text.encode("utf-8")).hexdigest()

                sub = Submission(
                    id=s["id"],
                    title=s["title"],
                    channel=s["channel"],
                    risk_tier=s["risk_tier"],
                    status="Draft",
                    creator_id=creator_id,
                    team_id="team-social",
                    is_synthetic=True,
                    created_at=now,
                    updated_at=now,
                )
                db.add(sub)
                db.flush()

                ver = SubmissionVersion(
                    submission_id=sub.id,
                    version_no=1,
                    content=content_text,
                    content_hash=content_hash,
                    created_by=creator_id,
                    source="creator",
                    created_at=now,
                )
                db.add(ver)
                db.flush()

                sub.current_version_id = ver.id
        db.commit()

        record_audit(
            db=db,
            action="system_seed_loaded",
            entity_type="system",
            entity_id="root",
            actor_id=admin_id,
            actor_role="admin",
            details={
                "teams": len(SEED_TEAMS),
                "users": len(SEED_USERS),
                "kb_entries": len(all_kb_entries),
                "samples": len(SEED_SAMPLES),
            },
        )
        print(f"[Seed] Successfully seeded {len(all_kb_entries)} KB entries and 5 samples S1-S5.")
    finally:
        if close_at_end:
            db.close()


if __name__ == "__main__":
    run_seed()
