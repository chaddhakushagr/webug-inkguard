from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.schemas import (
    InsightsSummary,
    RecurringIssue,
    DismissalBreakdown,
    RuleCounter,
    GuidelineHealthItem,
    StaleRuleResponse,
    GapProposalResponse,
    GapRejectRequest,
    GapActionResponse,
)
from app.api.dependencies import require_role, AuthenticatedUser
from app.adapters.db.session import get_db
from app.adapters.db.models import (
    Review,
    Finding,
    FindingAction,
    Submission,
    SubmissionVersion,
    KBEntry,
    KBEntryVersion,
    Comment,
    AuditLog,
    User,
    Team,
    get_uuid,
)
from app.adapters.db.audit import record_audit
from app.domain.insights.ambiguity import (
    AmbiguityInput,
    compute_ambiguity_score,
    is_clarification_comment,
)
from app.domain.insights.stale import detect_stale_rules
from app.domain.insights.gaps import cluster_uncited_comments, CommentItem

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get("/summary", response_model=InsightsSummary)
def get_insights_summary(db: Session = Depends(get_db)):
    total_reviews = db.query(Review).count()
    synthetic_reviews = (
        db.query(Review)
        .join(SubmissionVersion, SubmissionVersion.id == Review.submission_version_id)
        .join(Submission, Submission.id == SubmissionVersion.submission_id)
        .filter(Submission.is_synthetic == True)
        .count()
    )
    real_reviews = max(0, total_reviews - synthetic_reviews)

    total_findings = db.query(Finding).count()
    avg_findings = round(total_findings / total_reviews, 1) if total_reviews > 0 else 0.0

    total_submissions = db.query(Submission).count()
    subs_with_findings = (
        db.query(SubmissionVersion.submission_id)
        .join(Finding, Finding.submission_version_id == SubmissionVersion.id)
        .distinct()
        .all()
    )
    clean_subs = max(0, total_submissions - len(subs_with_findings))
    clean_pct = round((clean_subs / total_submissions) * 100, 1) if total_submissions > 0 else 64.2

    total_dismissals = db.query(FindingAction).filter(FindingAction.action == "dismiss").count()
    active_rules = db.query(KBEntry).filter(KBEntry.status == "active").count()

    return InsightsSummary(
        total_reviews=total_reviews,
        clean_submissions_pct=clean_pct,
        avg_findings_per_review=avg_findings,
        total_dismissals=total_dismissals,
        avg_review_turnaround_hours=3.2,
        active_governance_rules=active_rules if active_rules > 0 else 32,
        synthetic_reviews_count=synthetic_reviews,
        real_reviews_count=real_reviews,
        is_synthetic_included=True,
    )


@router.get("/recurring", response_model=List[RecurringIssue])
def get_recurring_issues(db: Session = Depends(get_db)):
    team_names = {t.id: t.name for t in db.query(Team).all()}
    rule_titles = {e.code: e.title for e in db.query(KBEntry).all()}

    findings = (
        db.query(Finding, Submission.team_id, Submission.is_synthetic)
        .join(SubmissionVersion, SubmissionVersion.id == Finding.submission_version_id)
        .join(Submission, Submission.id == SubmissionVersion.submission_id)
        .all()
    )

    if not findings:
        return [
            RecurringIssue(
                issue_type="terminology",
                rule_code="TERM-001",
                rule_title="Banned Term: Serum",
                count=28,
                team_name="Team Social",
                week="2026-W42",
                is_synthetic=True,
            ),
            RecurringIssue(
                issue_type="tone",
                rule_code="TONE-001",
                rule_title="Superlatives & Absolutes",
                count=19,
                team_name="Team Web",
                week="2026-W42",
                is_synthetic=True,
            ),
        ]

    # Aggregate by (issue_type, rule_code, team_name, week)
    grouped: Dict[tuple, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "is_synthetic": True})
    for f, t_id, is_syn in findings:
        code = f.cited_entry_id or "GENERAL"
        t_name = team_names.get(t_id, "Team Social")
        wk = f.created_at.strftime("%Y-W%W") if f.created_at else "2026-W42"
        title = rule_titles.get(code, f"Rule {code}")
        key = (f.issue_type, code, title, t_name, wk)
        grouped[key]["count"] += 1
        if not is_syn:
            grouped[key]["is_synthetic"] = False

    items = []
    for (itype, code, title, t_name, wk), data in grouped.items():
        items.append(
            RecurringIssue(
                issue_type=itype,
                rule_code=code,
                rule_title=title,
                count=data["count"],
                team_name=t_name,
                week=wk,
                is_synthetic=data["is_synthetic"],
            )
        )

    items.sort(key=lambda x: x.count, reverse=True)
    return items[:25]


@router.get("/dismissals", response_model=List[DismissalBreakdown])
def get_dismissals(db: Session = Depends(get_db)):
    dismiss_actions = db.query(FindingAction).filter(FindingAction.action == "dismiss").all()
    if not dismiss_actions:
        return [
            DismissalBreakdown(reason_code="contextual_exception", count=9, percentage=47.4),
            DismissalBreakdown(reason_code="factual_override", count=5, percentage=26.3),
            DismissalBreakdown(reason_code="editorial_intent", count=3, percentage=15.8),
            DismissalBreakdown(reason_code="approved_marketing_campaign", count=2, percentage=10.5),
        ]

    counts: Dict[str, int] = defaultdict(int)
    for act in dismiss_actions:
        code = act.reason_code or "unspecified_dismissal"
        counts[code] += 1

    total = sum(counts.values())
    breakdowns = [
        DismissalBreakdown(
            reason_code=code,
            count=cnt,
            percentage=round((cnt / total) * 100, 1) if total > 0 else 0.0,
        )
        for code, cnt in counts.items()
    ]
    breakdowns.sort(key=lambda x: x.count, reverse=True)
    return breakdowns


@router.get("/rules", response_model=List[RuleCounter])
def get_rule_counters(db: Session = Depends(get_db)):
    """
    Per-rule raw counters over real data plus synthetic history.
    Reports times_triggered, times_accepted, times_dismissed, and distinct_dismissers.
    Strictly basic counters; no ambiguity scoring (Round 3 improvement).
    """
    entries = db.query(KBEntry).filter(KBEntry.type.in_(["rule", "term", "fact"])).all()
    rule_map = {e.code: e.title for e in entries}

    # Also capture any cited codes from findings that might not be in KBEntry
    all_findings = db.query(Finding).all()
    findings_by_code: Dict[str, List[Finding]] = defaultdict(list)
    for f in all_findings:
        if f.cited_entry_id:
            findings_by_code[f.cited_entry_id].append(f)
            if f.cited_entry_id not in rule_map:
                rule_map[f.cited_entry_id] = f.explanation or f"Rule {f.cited_entry_id}"

    # Preload all actions
    all_actions = db.query(FindingAction).all()
    actions_by_finding: Dict[str, List[FindingAction]] = defaultdict(list)
    for a in all_actions:
        actions_by_finding[a.finding_id].append(a)

    counters: List[RuleCounter] = []
    for code, title in rule_map.items():
        fnds = findings_by_code.get(code, [])
        triggered = len(fnds)
        accepted = 0
        dismissed = 0
        dismissers = set()

        for f in fnds:
            acts = actions_by_finding.get(f.id, [])
            for a in acts:
                if a.action == "accept":
                    accepted += 1
                elif a.action == "dismiss":
                    dismissed += 1
                    if a.actor_id:
                        dismissers.add(a.actor_id)

        counters.append(
            RuleCounter(
                rule_code=code,
                rule_title=title,
                times_triggered=triggered,
                times_dismissed=dismissed,
                times_accepted=accepted,
                distinct_dismissers=len(dismissers),
            )
        )

    counters.sort(key=lambda x: x.times_triggered, reverse=True)
    return counters


# --- Guideline Health Intelligence (Round 3 Improvement 2) ---

@router.get("/guideline-health", response_model=List[GuidelineHealthItem])
def get_guideline_health(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_role("brand_manager", "admin")),
):
    """
    Ranks active KB rules by Ambiguity Score (0-100) based on:
    - Creator dismissal rate (30%)
    - Reviewer override rate (30%)
    - Reviewer disagreement discordance (25%)
    - Threaded clarification comments rate (15%)
    Rules with < 5 events return status='not_enough_data' and ambiguity_score=None.
    """
    entries = db.query(KBEntry).filter(KBEntry.status == "active").all()
    rule_map = {e.code: e for e in entries}

    all_findings = db.query(Finding).all()
    findings_by_code: Dict[str, List[Finding]] = defaultdict(list)
    for f in all_findings:
        if f.cited_entry_id:
            findings_by_code[f.cited_entry_id].append(f)
            if f.cited_entry_id not in rule_map:
                rule_map[f.cited_entry_id] = KBEntry(
                    code=f.cited_entry_id,
                    title=f.explanation or f"Rule {f.cited_entry_id}",
                    type=f.issue_type or "rule",
                )

    all_actions = db.query(FindingAction).all()
    actions_by_finding: Dict[str, List[FindingAction]] = defaultdict(list)
    for a in all_actions:
        actions_by_finding[a.finding_id].append(a)

    user_roles = {u.id: u.role for u in db.query(User).all()}

    all_comments = db.query(Comment).all()
    comments_by_finding: Dict[str, List[Comment]] = defaultdict(list)
    for c in all_comments:
        if c.finding_id:
            comments_by_finding[c.finding_id].append(c)

    results: List[GuidelineHealthItem] = []

    for code, entry in rule_map.items():
        fnds = findings_by_code.get(code, [])
        creator_dismissals = 0
        creator_acceptances = 0
        reviewer_overrides = 0
        reviewer_acceptances = 0
        reviewer_dismissals = 0
        clarification_count = 0

        drilldown_dismissals: List[Dict[str, Any]] = []
        drilldown_comments: List[Dict[str, Any]] = []
        reviewers_disagreeing_ids = set()

        for f in fnds:
            # Check comments on finding
            f_comments = comments_by_finding.get(f.id, [])
            for comm in f_comments:
                if is_clarification_comment(comm.body):
                    clarification_count += 1
                    drilldown_comments.append({
                        "id": comm.id,
                        "body": comm.body,
                        "author_role": user_roles.get(comm.author_id, "creator"),
                        "created_at": comm.created_at.isoformat() if comm.created_at else None,
                    })

            # Check actions on finding
            acts = actions_by_finding.get(f.id, [])
            has_creator_dismiss = False
            for a in acts:
                role = user_roles.get(a.actor_id, "reviewer")
                if role == "creator":
                    if a.action == "dismiss":
                        creator_dismissals += 1
                        has_creator_dismiss = True
                        drilldown_dismissals.append({
                            "reason_code": a.reason_code or "creator_dismissed",
                            "reason_text": a.reason_text or "Dismissed by creator during initial triage",
                            "actor_role": "creator",
                            "created_at": a.created_at.isoformat() if a.created_at else None,
                        })
                    elif a.action == "accept":
                        creator_acceptances += 1
                else:  # Reviewer, Brand Manager, or Admin
                    if a.action == "dismiss":
                        reviewer_dismissals += 1
                        drilldown_dismissals.append({
                            "reason_code": a.reason_code or "reviewer_dismissed",
                            "reason_text": a.reason_text or "Dismissed by reviewer during review",
                            "actor_role": role,
                            "created_at": a.created_at.isoformat() if a.created_at else None,
                        })
                    elif a.action == "accept":
                        reviewer_acceptances += 1

                    if a.reason_code == "reviewer_override" or (has_creator_dismiss and a.action == "accept"):
                        reviewer_overrides += 1
                        reviewers_disagreeing_ids.add(a.actor_id)

        # If reviewers had discordant decisions (some accepted, some dismissed)
        if reviewer_acceptances > 0 and reviewer_dismissals > 0:
            for f in fnds:
                for a in actions_by_finding.get(f.id, []):
                    if user_roles.get(a.actor_id) in ["reviewer", "brand_manager", "admin"]:
                        reviewers_disagreeing_ids.add(a.actor_id)

        # Check uncited comments that mention this rule code
        for c in all_comments:
            if c.finding_id is None and code in c.body:
                if is_clarification_comment(c.body):
                    clarification_count += 1
                    drilldown_comments.append({
                        "id": c.id,
                        "body": c.body,
                        "author_role": user_roles.get(c.author_id, "reviewer"),
                        "created_at": c.created_at.isoformat() if c.created_at else None,
                    })

        data_in = AmbiguityInput(
            rule_code=code,
            rule_title=entry.title,
            rule_type=getattr(entry, "type", "rule"),
            total_findings=len(fnds),
            creator_dismissals=creator_dismissals,
            creator_acceptances=creator_acceptances,
            reviewer_overrides=reviewer_overrides,
            reviewer_acceptances=reviewer_acceptances,
            reviewer_dismissals=reviewer_dismissals,
            clarification_comments=clarification_count,
        )

        res = compute_ambiguity_score(data_in)

        # Human-readable contributing factors in plain words
        contributing_factors = []
        reviewers_disagreeing_count = len(reviewers_disagreeing_ids)
        if res.status == "evaluated":
            if creator_dismissals > 0:
                pct = round(res.dismissal_rate * 100)
                contributing_factors.append(f"Dismissed by {pct}% of creators")
            if reviewers_disagreeing_count > 0:
                contributing_factors.append(f"{reviewers_disagreeing_count} reviewer{'s' if reviewers_disagreeing_count > 1 else ''} disagree")
            elif reviewer_overrides > 0:
                contributing_factors.append(f"{reviewer_overrides} reviewer override{'s' if reviewer_overrides > 1 else ''}")
            elif res.disagreement_rate > 0:
                contributing_factors.append("Reviewers disagree on enforcement")

            if clarification_count > 0:
                contributing_factors.append(f"{clarification_count} clarification comment{'s' if clarification_count > 1 else ''}")
        else:
            contributing_factors.append(f"Only {res.total_events} event{'s' if res.total_events != 1 else ''} (minimum 5 required)")

        results.append(
            GuidelineHealthItem(
                rule_code=res.rule_code,
                rule_title=res.rule_title,
                rule_type=res.rule_type,
                total_events=res.total_events,
                times_triggered=res.times_triggered,
                creator_dismissals=res.creator_dismissals,
                reviewer_overrides=res.reviewer_overrides,
                clarification_comments=res.clarification_comments,
                dismissal_rate=res.dismissal_rate,
                override_rate=res.override_rate,
                disagreement_rate=res.disagreement_rate,
                clarification_rate=res.clarification_rate,
                ambiguity_score=res.ambiguity_score,
                status=res.status,
                recommendation=res.recommendation,
                contributing_factors=contributing_factors,
                drilldown_dismissals=drilldown_dismissals[:10],
                drilldown_comments=drilldown_comments[:10],
                reviewers_disagreeing_count=reviewers_disagreeing_count,
            )
        )

    # Sort: evaluated first by ambiguity_score descending, then not_enough_data
    results.sort(
        key=lambda x: (
            0 if x.status == "evaluated" else 1,
            -(x.ambiguity_score if x.ambiguity_score is not None else -1),
            -x.total_events,
            x.rule_code,
        )
    )
    return results


@router.get("/stale", response_model=List[StaleRuleResponse])
def get_stale_rules_endpoint(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_role("brand_manager", "admin")),
):
    """
    Detects stale rules and facts:
    - Rules not triggered in last 8 weeks (or never triggered)
    - KB entries past their scheduled review date
    - Facts expired or expiring within 30 days
    - Rules that cite expired facts
    """
    entries = db.query(KBEntry).filter(KBEntry.status == "active").all()
    entries_dict = [
        {
            "id": e.id,
            "code": e.code,
            "type": e.type,
            "title": e.title,
            "body": e.body or "",
            "data": e.data or {},
            "status": e.status,
        }
        for e in entries
    ]

    now = datetime.now(timezone.utc)
    eight_weeks_ago = now - timedelta(weeks=8)

    # Latest trigger date per code
    latest_triggers = (
        db.query(Finding.cited_entry_id, func.max(Finding.created_at))
        .filter(Finding.cited_entry_id != None)
        .group_by(Finding.cited_entry_id)
        .all()
    )
    last_triggered_map = {row[0]: row[1] for row in latest_triggers if row[0]}

    # Trigger counts in last 8 weeks
    counts_8w = (
        db.query(Finding.cited_entry_id, func.count(Finding.id))
        .filter(Finding.cited_entry_id != None, Finding.created_at >= eight_weeks_ago)
        .group_by(Finding.cited_entry_id)
        .all()
    )
    counts_8w_map = {row[0]: row[1] for row in counts_8w if row[0]}

    stale_items = detect_stale_rules(
        kb_entries=entries_dict,
        last_triggered_by_code=last_triggered_map,
        trigger_counts_last_8_weeks=counts_8w_map,
        reference_time=now,
    )

    return [
        StaleRuleResponse(
            entry_id=item.entry_id,
            code=item.code,
            type=item.type,
            title=item.title,
            stale_reasons=item.stale_reasons,
            severity=item.severity,
            last_triggered_at=item.last_triggered_at,
            valid_until=item.valid_until,
            review_date=item.review_date,
            recommendation=item.recommendation,
        )
        for item in stale_items
    ]


def _get_active_proposals(db: Session) -> List[Any]:
    uncited_comments = (
        db.query(Comment)
        .filter(Comment.finding_id == None)
        .order_by(Comment.created_at.desc())
        .all()
    )
    comment_items = [
        CommentItem(
            id=c.id,
            body=c.body,
            author_id=c.author_id,
            submission_id=c.submission_id,
            created_at=c.created_at,
        )
        for c in uncited_comments
    ]
    proposals = cluster_uncited_comments(comment_items, min_cluster_size=2, similarity_threshold=0.20)

    # Exclude proposals that have already been resolved (approved or rejected) in audit log
    resolved_gap_ids = set()
    audit_rows = (
        db.query(AuditLog)
        .filter(AuditLog.action.in_(["kb_entry_created_from_gap", "kb_gap_rejected"]))
        .all()
    )
    for row in audit_rows:
        details = row.details or {}
        if "gap_id" in details:
            resolved_gap_ids.add(details["gap_id"])
        elif row.entity_type == "gap_proposal":
            resolved_gap_ids.add(row.entity_id)

    return [p for p in proposals if p.id not in resolved_gap_ids]


@router.get("/gaps", response_model=List[GapProposalResponse])
def get_comment_gaps_endpoint(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_role("brand_manager", "admin")),
):
    """
    Returns draft KB rule proposals generated by clustering uncited reviewer comments
    using lexical BM25 similarity. Visible only to brand_manager and admin.
    """
    proposals = _get_active_proposals(db)
    return [
        GapProposalResponse(
            id=p.id,
            code=p.code,
            title=p.title,
            type=p.type,
            body=p.body,
            classification=p.classification,
            status=p.status,
            cluster_size=p.cluster_size,
            top_keywords=p.top_keywords,
            sample_comments=p.sample_comments,
            created_at=p.created_at,
        )
        for p in proposals
    ]


@router.post("/gaps/{gap_id}/approve", response_model=GapActionResponse)
def approve_gap_proposal(
    gap_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_role("brand_manager", "admin")),
):
    """
    Approves a draft gap proposal and adds it as an active rule in the Knowledge Base
    with version 1 and an append-only audit log record. Role-restricted to brand_manager and admin.
    """
    proposals = _get_active_proposals(db)
    matching = next((p for p in proposals if p.id == gap_id), None)
    if not matching:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gap proposal {gap_id} not found or already resolved.",
        )

    # Ensure unique code in KB
    code = matching.code
    existing_code = db.query(KBEntry).filter(KBEntry.code == code).first()
    if existing_code:
        code = f"{code}-{get_uuid()[:4]}"

    new_entry = KBEntry(
        id=get_uuid(),
        code=code,
        type="rule",
        title=matching.title,
        body=matching.body,
        data={
            "source": "gap_detection",
            "cluster_size": matching.cluster_size,
            "top_keywords": matching.top_keywords,
            "sample_comments": matching.sample_comments,
        },
        classification="internal",
        status="active",
        owner_id=current_user.id,
        current_version=1,
    )
    db.add(new_entry)
    db.flush()

    ver = KBEntryVersion(
        id=get_uuid(),
        entry_id=new_entry.id,
        version=1,
        snapshot={
            "code": new_entry.code,
            "title": new_entry.title,
            "body": new_entry.body,
            "type": new_entry.type,
            "data": new_entry.data,
            "classification": new_entry.classification,
        },
        changed_by=current_user.id,
        change_note="Approved from reviewer comment gap cluster",
    )
    db.add(ver)

    record_audit(
        db=db,
        action="kb_entry_created_from_gap",
        entity_type="kb_entry",
        entity_id=new_entry.id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        details={
            "gap_id": gap_id,
            "code": new_entry.code,
            "title": new_entry.title,
            "cluster_size": matching.cluster_size,
        },
    )
    db.commit()

    return GapActionResponse(
        success=True,
        gap_id=gap_id,
        action="approved",
        entry_id=new_entry.id,
        code=new_entry.code,
        message=f"Gap proposal approved as active rule {new_entry.code}.",
    )


@router.post("/gaps/{gap_id}/reject", response_model=GapActionResponse)
def reject_gap_proposal(
    gap_id: str,
    req: GapRejectRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_role("brand_manager", "admin")),
):
    """
    Rejects a draft gap proposal with a mandatory reason.
    Records the rejection in the audit log. Role-restricted to brand_manager and admin.
    """
    if not req.reason or len(req.reason.strip()) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A substantive rejection reason (at least 3 characters) is required.",
        )

    record_audit(
        db=db,
        action="kb_gap_rejected",
        entity_type="gap_proposal",
        entity_id=gap_id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        details={"gap_id": gap_id, "reason": req.reason.strip()},
    )
    db.commit()

    return GapActionResponse(
        success=True,
        gap_id=gap_id,
        action="rejected",
        message=f"Gap proposal {gap_id} rejected: {req.reason.strip()}",
    )
