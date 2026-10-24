from fastapi import APIRouter
from typing import List
from app.api.schemas import (
    InsightsSummary,
    RecurringIssue,
    DismissalBreakdown,
    RuleCounter,
)

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get("/summary", response_model=InsightsSummary)
def get_insights_summary():
    return InsightsSummary(
        total_reviews=84,
        clean_submissions_pct=64.2,
        avg_findings_per_review=1.8,
        total_dismissals=19,
        avg_review_turnaround_hours=3.4,
        active_governance_rules=32,
    )


@router.get("/recurring", response_model=List[RecurringIssue])
def get_recurring_issues():
    return [
        RecurringIssue(
            issue_type="terminology",
            rule_code="TERM-001",
            rule_title="Banned Term: Serum",
            count=28,
            team_name="Team Social",
            week="2026-W42",
        ),
        RecurringIssue(
            issue_type="tone",
            rule_code="TONE-001",
            rule_title="Superlatives & Absolutes",
            count=19,
            team_name="Team Web",
            week="2026-W42",
        ),
        RecurringIssue(
            issue_type="claim",
            rule_code="FACT-001",
            rule_title="Clinical Trial Claim Entailment",
            count=12,
            team_name="Team PR",
            week="2026-W41",
        ),
    ]


@router.get("/dismissals", response_model=List[DismissalBreakdown])
def get_dismissals():
    return [
        DismissalBreakdown(reason_code="contextual_exception", count=9, percentage=47.4),
        DismissalBreakdown(reason_code="factual_override", count=5, percentage=26.3),
        DismissalBreakdown(reason_code="editorial_intent", count=3, percentage=15.8),
        DismissalBreakdown(reason_code="approved_marketing_campaign", count=2, percentage=10.5),
    ]


@router.get("/rules", response_model=List[RuleCounter])
def get_rule_counters():
    return [
        RuleCounter(
            rule_code="TERM-001",
            rule_title="Banned Term: Serum",
            times_triggered=35,
            times_dismissed=4,
            times_accepted=31,
        ),
        RuleCounter(
            rule_code="TONE-001",
            rule_title="Superlatives & Miracle Claims",
            times_triggered=24,
            times_dismissed=12,
            times_accepted=12,
        ),
        RuleCounter(
            rule_code="FACT-001",
            rule_title="Hydration Improvement Trial Claim",
            times_triggered=18,
            times_dismissed=2,
            times_accepted=16,
        ),
    ]
