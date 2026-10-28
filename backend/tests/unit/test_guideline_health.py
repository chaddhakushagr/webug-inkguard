"""
Unit tests for Guideline Health domain logic (Round 3 Improvement 2).
Pure Python tests verifying:
- Ambiguity formula with exact hand-computed values
- Minimum-sample behaviour (< 5 events -> not_enough_data)
- Stale rule and fact detection across all 4 criteria
- BM25 comment gap clustering and deterministic draft generation
"""

from datetime import datetime, date, timedelta, timezone
import pytest

from app.domain.insights.ambiguity import (
    AmbiguityInput,
    AmbiguityResult,
    compute_ambiguity_score,
    is_clarification_comment,
)
from app.domain.insights.stale import (
    StaleRuleItem,
    detect_stale_rules,
)
from app.domain.insights.gaps import (
    CommentItem,
    DraftKBEntryProposal,
    cluster_uncited_comments,
    tokenize,
)


def test_ambiguity_hand_computed_worked_example():
    """
    Verifies the exact worked example documented in docs/GUIDELINE_HEALTH.md:
    - 20 findings
    - 13 creator dismissals (r_dismiss = 0.65)
    - 8 reviewer overrides (r_override = 0.40)
    - Reviewers: 6 acceptances, 9 dismissals (r_disagree = 4 * 0.4 * 0.6 = 0.96)
    - 5 clarification comments (r_clarify = 5 / 20 = 0.25)
    - Raw score: 30*0.65 + 30*0.40 + 25*0.96 + 15*0.25 = 19.5 + 12.0 + 24.0 + 3.75 = 59.25
    - Expected rounded score = 59
    """
    data = AmbiguityInput(
        rule_code="RULE-AMBIG-01",
        rule_title="Avoid Excessive Superlatives in Headlines",
        rule_type="rule",
        total_findings=20,
        creator_dismissals=13,
        creator_acceptances=7,
        reviewer_overrides=8,
        reviewer_acceptances=6,
        reviewer_dismissals=9,
        clarification_comments=5,
    )
    result = compute_ambiguity_score(data)
    assert result.status == "evaluated"
    assert result.total_events == 25
    assert result.dismissal_rate == 0.65
    assert result.override_rate == 0.4
    assert result.disagreement_rate == 0.96
    assert result.clarification_rate == 0.25
    assert result.ambiguity_score == 59


def test_ambiguity_minimum_sample_threshold():
    """
    Asserts that rules with < 5 total events strictly return
    status='not_enough_data' and ambiguity_score=None.
    """
    # 4 findings, 0 comments (total 4 < 5)
    data = AmbiguityInput(
        rule_code="TERM-001",
        rule_title="Banned Term: Serum",
        total_findings=4,
        creator_dismissals=4,
        clarification_comments=0,
    )
    res = compute_ambiguity_score(data)
    assert res.status == "not_enough_data"
    assert res.ambiguity_score is None

    # 2 findings, 2 comments (total 4 < 5)
    data2 = AmbiguityInput(
        rule_code="TERM-002",
        rule_title="Banned Term: Rosehip Oil",
        total_findings=2,
        clarification_comments=2,
    )
    res2 = compute_ambiguity_score(data2)
    assert res2.status == "not_enough_data"
    assert res2.ambiguity_score is None

    # Exactly 5 events: must evaluate!
    data3 = AmbiguityInput(
        rule_code="TERM-003",
        rule_title="Banned Term: Miracle",
        total_findings=5,
        creator_dismissals=0,
        creator_acceptances=5,
        reviewer_overrides=0,
        reviewer_acceptances=5,
        reviewer_dismissals=0,
        clarification_comments=0,
    )
    res3 = compute_ambiguity_score(data3)
    assert res3.status == "evaluated"
    assert res3.ambiguity_score == 0  # Perfect consensus


def test_ambiguity_extreme_scores():
    """Verifies bounds [0, 100] on perfect vs maximally frictioned rules."""
    # Maximal friction: all dismissals, all overrides, 50/50 disagreement, many questions
    max_friction = AmbiguityInput(
        rule_code="RULE-CHAOS",
        rule_title="Unclear Direction",
        total_findings=10,
        creator_dismissals=10,  # r_dismiss = 1.0 (30 pts)
        reviewer_overrides=10,  # r_override = 1.0 (30 pts)
        reviewer_acceptances=5,
        reviewer_dismissals=5,  # r_disagree = 1.0 (25 pts)
        clarification_comments=10,  # r_clarify = 1.0 (15 pts)
    )
    res_max = compute_ambiguity_score(max_friction)
    assert res_max.ambiguity_score == 100

    # Minimal friction: 0 dismissals, 0 overrides, unanimous reviewers, 0 questions
    min_friction = AmbiguityInput(
        rule_code="RULE-CLEAR",
        rule_title="Clear Direction",
        total_findings=20,
        creator_dismissals=0,
        creator_acceptances=20,
        reviewer_overrides=0,
        reviewer_acceptances=20,
        reviewer_dismissals=0,
        clarification_comments=0,
    )
    res_min = compute_ambiguity_score(min_friction)
    assert res_min.ambiguity_score == 0


def test_clarification_comment_detection():
    """Verifies clarification keyword matching."""
    assert is_clarification_comment("Could you clarify if this rule applies here?") is True
    assert is_clarification_comment("Is this an exception?") is True
    assert is_clarification_comment("Why did this flag as ambiguous?") is True
    assert is_clarification_comment("Unclear what preferred term to use here.") is True
    assert is_clarification_comment("Approved copy for publication.") is False
    assert is_clarification_comment("") is False


def test_stale_rule_detection():
    """Verifies all 4 stale detection criteria."""
    ref_time = datetime(2026, 10, 28, 12, 0, 0, tzinfo=timezone.utc)
    
    kb_entries = [
        # 1. Active rule never triggered
        {
            "id": "e1",
            "code": "RULE-UNUSED-01",
            "type": "rule",
            "title": "Unused Rule",
            "status": "active",
            "data": {},
        },
        # 2. Rule past its review date
        {
            "id": "e2",
            "code": "RULE-OVERDUE-01",
            "type": "rule",
            "title": "Overdue Rule",
            "status": "active",
            "data": {"review_date": "2026-05-01"},
        },
        # 3. Fact already expired
        {
            "id": "e3",
            "code": "FACT-EXPIRED-01",
            "type": "fact",
            "title": "Expired Trial Evidence",
            "status": "active",
            "data": {"valid_until": "2025-12-31"},
        },
        # 4. Fact expiring within 30 days
        {
            "id": "e4",
            "code": "FACT-SOON-01",
            "type": "fact",
            "title": "Expiring Trial",
            "status": "active",
            "data": {"valid_until": "2026-11-10"},
        },
        # 5. Rule that cites expired fact
        {
            "id": "e5",
            "code": "RULE-CLAIM-EXPIRED",
            "type": "rule",
            "title": "Clinical Efficacy Rule",
            "status": "active",
            "body": "Claims must cite FACT-EXPIRED-01 for proof.",
            "data": {},
        },
        # 6. Fresh active rule triggered recently
        {
            "id": "e6",
            "code": "TERM-FRESH",
            "type": "term",
            "title": "Active Term",
            "status": "active",
            "data": {"review_date": "2027-01-01"},
        },
    ]

    last_triggered = {
        "TERM-FRESH": ref_time - timedelta(days=2),
    }
    trigger_counts_8w = {
        "TERM-FRESH": 15,
    }

    stale_items = detect_stale_rules(
        kb_entries=kb_entries,
        last_triggered_by_code=last_triggered,
        trigger_counts_last_8_weeks=trigger_counts_8w,
        reference_time=ref_time,
    )

    stale_codes = {item.code: item for item in stale_items}

    # e1: never triggered
    assert "RULE-UNUSED-01" in stale_codes
    assert any("never_triggered" in r for r in stale_codes["RULE-UNUSED-01"].stale_reasons)

    # e2: past review date
    assert "RULE-OVERDUE-01" in stale_codes
    assert any("past_review_date" in r for r in stale_codes["RULE-OVERDUE-01"].stale_reasons)

    # e3: fact expired
    assert "FACT-EXPIRED-01" in stale_codes
    assert any("fact_expired" in r for r in stale_codes["FACT-EXPIRED-01"].stale_reasons)
    assert stale_codes["FACT-EXPIRED-01"].severity == "high"

    # e4: fact expiring soon
    assert "FACT-SOON-01" in stale_codes
    assert any("fact_expiring_soon" in r for r in stale_codes["FACT-SOON-01"].stale_reasons)

    # e5: cites expired fact
    assert "RULE-CLAIM-EXPIRED" in stale_codes
    assert any("cites_expired_facts: FACT-EXPIRED-01" in r for r in stale_codes["RULE-CLAIM-EXPIRED"].stale_reasons)
    assert stale_codes["RULE-CLAIM-EXPIRED"].severity == "high"

    # e6: fresh active rule should NOT be stale
    assert "TERM-FRESH" not in stale_codes


def test_comment_gap_clustering():
    """Verifies BM25 clustering of uncited reviewer comments into draft rules."""
    comments = [
        # Cluster 1: Packaging & FSC
        CommentItem(id="c1", body="Please include FSC certified packaging note on all product carton boxes.", author_id="u1", submission_id="s1"),
        CommentItem(id="c2", body="Missing required FSC logo certification on recycled retail packaging.", author_id="u2", submission_id="s2"),
        CommentItem(id="c3", body="Packaging copy must explicitly specify FSC certified recycled materials.", author_id="u3", submission_id="s3"),
        # Cluster 2: EU VAT & Shipping
        CommentItem(id="c4", body="European international shipping orders require VAT customs disclosure at checkout.", author_id="u1", submission_id="s4"),
        CommentItem(id="c5", body="Add clear EU VAT customs notification for international European shipping orders.", author_id="u2", submission_id="s5"),
        # Singleton comment (should not form a cluster)
        CommentItem(id="c6", body="Font size on Instagram story is too small for mobile legibility.", author_id="u1", submission_id="s6"),
    ]

    proposals = cluster_uncited_comments(comments, min_cluster_size=2, similarity_threshold=0.20)
    assert len(proposals) >= 2

    # Verify cluster 1 (Packaging / FSC)
    pkg_proposals = [p for p in proposals if any("packaging" in k or "fsc" in k for k in p.top_keywords)]
    assert len(pkg_proposals) >= 1
    pkg = pkg_proposals[0]
    assert pkg.cluster_size >= 2
    assert pkg.status == "draft"
    assert pkg.type == "rule"
    assert "FSC" in pkg.body or "packaging" in pkg.body.lower()

    # Verify cluster 2 (VAT / Shipping)
    vat_proposals = [p for p in proposals if any("vat" in k or "shipping" in k for k in p.top_keywords)]
    assert len(vat_proposals) >= 1
    vat = vat_proposals[0]
    assert vat.cluster_size >= 2
    assert vat.status == "draft"
