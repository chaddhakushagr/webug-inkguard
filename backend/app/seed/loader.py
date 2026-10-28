"""
Idempotent seed data loader for Inkguard.
Populates teams, demo users, initial Lumo brand knowledge base, and sample submissions S1-S5.
Safe to run repeatedly without duplicate key errors or data drift.
"""

import hashlib
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.adapters.db.session import engine, SessionLocal, Base
from app.adapters.db.models import (
    Team,
    User,
    KBEntry,
    KBEntryVersion,
    Submission,
    SubmissionVersion,
    Review,
    Finding,
    FindingAction,
    Comment,
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
    generate_synthetic_history,
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

        print("[Seed] 5. Loading synthetic review history (8 weeks, 4 teams, 80 reviews)...")
        has_modern_actions = db.query(FindingAction).filter(FindingAction.id.like("act-c-syn-rev-%")).first()
        if not has_modern_actions:
            # Refresh old synthetic review history with creator actions and clarification comments
            syn_subs = db.query(Submission).filter(Submission.id.like("syn-sub-%")).all()
            for s in syn_subs:
                vers = db.query(SubmissionVersion).filter(SubmissionVersion.submission_id == s.id).all()
                for v in vers:
                    revs = db.query(Review).filter(Review.submission_version_id == v.id).all()
                    for r in revs:
                        fnds = db.query(Finding).filter(Finding.review_id == r.id).all()
                        for f in fnds:
                            db.query(FindingAction).filter(FindingAction.finding_id == f.id).delete()
                            db.query(Comment).filter(Comment.finding_id == f.id).delete()
                            db.delete(f)
                        db.delete(r)
                    db.delete(v)
                db.delete(s)
            db.commit()

        existing_syn_count = db.query(Submission).filter(Submission.id.like("syn-sub-%")).count()
        if existing_syn_count < 80:
            history_items = generate_synthetic_history(weeks=8, total_reviews=80)
            team_map = {
                "Team Social": "team-social",
                "Team Web & Growth": "team-web",
                "Team PR & Communications": "team-pr",
                "Brand Strategy": "team-brand",
            }
            reviewer_map = {
                "reviewer.sarah@lumo.internal": "u-reviewer-1",
                "reviewer.alex@lumo.internal": "u-reviewer-2",
                "manager.kavita@lumo.internal": "u-manager",
            }
            creator_map = {
                "creator.social@lumo.internal": "u-creator-social",
                "creator.web@lumo.internal": "u-creator-web",
                "creator.maya@lumo.internal": "u-creator-maya",
            }
            channels = ["social", "email", "blog", "web"]
            for idx, item in enumerate(history_items):
                existing_item = db.query(Submission).filter(Submission.id == item["submission_id"]).first()
                if not existing_item:
                    try:
                        ts = datetime.fromisoformat(item["timestamp"])
                    except Exception:
                        ts = now

                    t_id = team_map.get(item["team"], "team-social")
                    c_id = creator_map.get(item["creator"], "u-creator-elena")
                    r_id = reviewer_map.get(item["reviewer"], "u-rev-marcus")
                    ch = channels[idx % len(channels)]

                    sub = Submission(
                        id=item["submission_id"],
                        title=item["submission_title"],
                        channel=ch,
                        risk_tier="medium" if "AMBIG" in item["rule_code"] else ("high" if "CLAIM" in item["rule_code"] else "low"),
                        status="Approved" if item["action"] in ["accept", "dismiss"] else "Changes Requested",
                        creator_id=c_id,
                        team_id=t_id,
                        is_synthetic=True,
                        created_at=ts,
                        updated_at=ts,
                    )
                    db.add(sub)
                    db.flush()

                    ver = SubmissionVersion(
                        id=f"ver-{item['submission_id']}",
                        submission_id=sub.id,
                        version_no=1,
                        content=f"Copy for {item['submission_title']}. Phrasing reviewed against {item['rule_code']}.",
                        content_hash=hashlib.sha256(item["submission_title"].encode("utf-8")).hexdigest(),
                        created_by=c_id,
                        source="creator",
                        created_at=ts,
                    )
                    db.add(ver)
                    db.flush()
                    sub.current_version_id = ver.id

                    rev = Review(
                        id=item["review_id"],
                        submission_version_id=ver.id,
                        status="completed",
                        mode="mock",
                        provider="mock",
                        model="mock",
                        prompt_version="v1",
                        started_at=ts,
                        finished_at=ts,
                    )
                    db.add(rev)
                    db.flush()

                    issue_type = "terminology" if item["rule_code"].startswith("TERM") else ("claim" if "CLAIM" in item["rule_code"] else ("missing_disclaimer" if "DISC" in item["rule_code"] else "tone"))
                    severity = "high" if "CLAIM" in item["rule_code"] else ("medium" if "AMBIG" in item["rule_code"] else "low")

                    fnd = Finding(
                        id=f"fnd-{item['review_id']}",
                        review_id=rev.id,
                        submission_version_id=ver.id,
                        fingerprint=hashlib.sha256(f"{item['rule_code']}-{ver.id}".encode("utf-8")).hexdigest()[:16],
                        source="rule" if item["rule_code"].startswith("RULE") or item["rule_code"].startswith("TERM") else "ai",
                        issue_type=issue_type,
                        severity=severity,
                        confidence=1.0,
                        span_start=0,
                        span_end=20,
                        excerpt=f"Text span citing {item['rule_code']}",
                        cited_entry_id=item["rule_code"],
                        is_policy=True,
                        explanation=f"Governance rule trigger for {item['rule_code']}",
                        status="accepted" if item["action"] == "accept" else ("dismissed" if item["action"] == "dismiss" else ("escalated" if item["action"] == "escalate" else "open")),
                        is_synthetic=True,
                        created_at=ts,
                    )
                    db.add(fnd)
                    db.flush()

                    # 1. Creator action
                    c_act = item.get("creator_action", item["action"])
                    act_c = FindingAction(
                        id=f"act-c-{item['review_id']}",
                        finding_id=fnd.id,
                        actor_id=c_id,
                        action=c_act,
                        reason_code=item.get("dismiss_reason") if c_act == "dismiss" else "creator_fix",
                        reason_text=item.get("comment") or "Recorded in creator triage",
                        created_at=ts,
                    )
                    db.add(act_c)

                    # 2. Reviewer action (if different or override)
                    r_act = item.get("reviewer_action", item["action"])
                    if r_act != c_act or item.get("is_override"):
                        act_r = FindingAction(
                            id=f"act-r-{item['review_id']}",
                            finding_id=fnd.id,
                            actor_id=r_id,
                            action=r_act,
                            reason_code="reviewer_override" if item.get("is_override") else ("approved_edit" if r_act == "accept" else item.get("dismiss_reason")),
                            reason_text="Reviewer override during content verification" if item.get("is_override") else (item.get("comment") or "Reviewer sign-off"),
                            created_at=ts + timedelta(minutes=15),
                        )
                        db.add(act_r)

                    # 3. Threaded clarification comment on finding
                    if item.get("clarification_question"):
                        comm = Comment(
                            id=f"comm-{item['review_id']}",
                            submission_id=sub.id,
                            finding_id=fnd.id,
                            author_id=c_id,
                            body=item["clarification_question"],
                            created_at=ts + timedelta(minutes=5),
                        )
                        db.add(comm)

            db.commit()
            print(f"[Seed] Successfully seeded {len(history_items)} synthetic reviews with findings and actions.")

        # Seed uncited reviewer comments that form gap clusters
        print("[Seed] 6. Seeding uncited reviewer comments for Gap Detection...")
        existing_gap_comments = db.query(Comment).filter(Comment.id.like("gap-comment-%")).count()
        if existing_gap_comments < 7:
            gap_comment_seeds = [
                # Cluster 1: Packaging & FSC Recycled Certification
                {
                    "id": "gap-comment-001",
                    "sub_id": "syn-sub-001",
                    "reviewer": "u-reviewer-1",
                    "text": "Please include FSC certified packaging disclosure on all printed carton boxes.",
                },
                {
                    "id": "gap-comment-002",
                    "sub_id": "syn-sub-002",
                    "reviewer": "u-reviewer-2",
                    "text": "Missing required FSC logo certification on recycled retail packaging units.",
                },
                {
                    "id": "gap-comment-003",
                    "sub_id": "syn-sub-003",
                    "reviewer": "u-reviewer-1",
                    "text": "Carton packaging copy must explicitly specify FSC certified recycled materials.",
                },
                {
                    "id": "gap-comment-004",
                    "sub_id": "syn-sub-004",
                    "reviewer": "u-manager",
                    "text": "Retail packaging compliance requires FSC mixed-sources certification mark on box flap.",
                },
                # Cluster 2: International Shipping & European Customs VAT
                {
                    "id": "gap-comment-005",
                    "sub_id": "syn-sub-005",
                    "reviewer": "u-reviewer-1",
                    "text": "European international shipping orders require VAT customs tax disclosure at checkout.",
                },
                {
                    "id": "gap-comment-006",
                    "sub_id": "syn-sub-006",
                    "reviewer": "u-reviewer-2",
                    "text": "Add clear EU VAT customs notification for international European shipping orders.",
                },
                {
                    "id": "gap-comment-007",
                    "sub_id": "syn-sub-007",
                    "reviewer": "u-manager",
                    "text": "International shipping policy must clarify EU VAT handling and customs duties.",
                },
            ]
            for gc in gap_comment_seeds:
                existing = db.query(Comment).filter(Comment.id == gc["id"]).first()
                if not existing:
                    c = Comment(
                        id=gc["id"],
                        submission_id=gc["sub_id"],
                        finding_id=None,
                        author_id=gc["reviewer"],
                        body=gc["text"],
                        created_at=now - timedelta(days=5),
                    )
                    db.add(c)
            db.commit()
            print("[Seed] Successfully seeded uncited reviewer comments for Gap Detection clusters.")

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
                "synthetic_reviews": 80,
            },
        )
        print(f"[Seed] Successfully seeded {len(all_kb_entries)} KB entries, 5 samples S1-S5, and 80 synthetic reviews.")
    finally:
        if close_at_end:
            db.close()


if __name__ == "__main__":
    run_seed()
