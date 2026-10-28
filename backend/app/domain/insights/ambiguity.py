"""
Pure Python domain module for Rule Ambiguity Scoring (Round 3 Improvement 2).
Zero web, database, or ML dependencies.

Formula:
Ambiguity Score (0-100) measures four friction signals:
1. Creator Dismissal Rate (w_dismiss = 30):
   r_dismiss = dismissals / total_findings
2. Reviewer Override Rate (w_override = 30):
   r_override = overrides / total_findings
   (Reviewer explicitly reverses/overrides a finding decision or creator action)
3. Reviewer Disagreement Rate (w_disagree = 25):
   Normalized variance of reviewer actions:
   r_disagree = 4 * (accepted_by_reviewers) * (dismissed_by_reviewers) / (total_reviewer_actions)^2
   Yields 1.0 when 50/50 split (maximal disagreement) and 0.0 when unanimous.
4. Clarification Comments Rate (w_clarify = 15):
   r_clarify = min(1.0, clarification_comments / max(1, total_findings))
   Comments containing confusion/clarification phrases ('?', 'clarify', 'unclear', 'exception').

Minimum Sample Rule:
If total_events < 5: return score=None, status="not_enough_data".
Otherwise:
score = round(30 * r_dismiss + 30 * r_override + 25 * r_disagree + 15 * r_clarify)
clamped to [0, 100].
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import re


CLARIFICATION_KEYWORDS = [
    r"\?",
    r"\bclarif",
    r"\bunclear\b",
    r"\bwhat about\b",
    r"\binterpret",
    r"\bexception\b",
    r"\bambiguous\b",
    r"\bconfus",
    r"\bwhy\b",
    r"\bhow to\b",
]

CLARIFICATION_REGEX = re.compile("|".join(CLARIFICATION_KEYWORDS), re.IGNORECASE)


@dataclass(frozen=True)
class AmbiguityInput:
    rule_code: str
    rule_title: str
    rule_type: str = "rule"
    total_findings: int = 0
    creator_dismissals: int = 0
    creator_acceptances: int = 0
    reviewer_overrides: int = 0
    reviewer_acceptances: int = 0
    reviewer_dismissals: int = 0
    clarification_comments: int = 0


@dataclass(frozen=True)
class AmbiguityResult:
    rule_code: str
    rule_title: str
    rule_type: str
    total_events: int
    times_triggered: int
    creator_dismissals: int
    reviewer_overrides: int
    clarification_comments: int
    dismissal_rate: float
    override_rate: float
    disagreement_rate: float
    clarification_rate: float
    ambiguity_score: Optional[int]
    status: str  # "evaluated" or "not_enough_data"
    recommendation: str


def is_clarification_comment(text: str) -> bool:
    """Checks whether a comment text indicates confusion or clarification on a rule."""
    if not text:
        return False
    return bool(CLARIFICATION_REGEX.search(text))


def compute_ambiguity_score(data: AmbiguityInput) -> AmbiguityResult:
    """
    Computes rule ambiguity score according to the specification.
    Returns AmbiguityResult with status="not_enough_data" if total_events < 5.
    """
    total_events = data.total_findings + data.clarification_comments

    # Minimum sample threshold
    if total_events < 5:
        return AmbiguityResult(
            rule_code=data.rule_code,
            rule_title=data.rule_title,
            rule_type=data.rule_type,
            total_events=total_events,
            times_triggered=data.total_findings,
            creator_dismissals=data.creator_dismissals,
            reviewer_overrides=data.reviewer_overrides,
            clarification_comments=data.clarification_comments,
            dismissal_rate=0.0,
            override_rate=0.0,
            disagreement_rate=0.0,
            clarification_rate=0.0,
            ambiguity_score=None,
            status="not_enough_data",
            recommendation="Insufficient review events (< 5) to compute ambiguity.",
        )

    # 1. Creator Dismissal Rate
    if data.total_findings > 0:
        r_dismiss = min(1.0, max(0.0, data.creator_dismissals / data.total_findings))
    else:
        r_dismiss = 0.0

    # 2. Reviewer Override Rate
    if data.total_findings > 0:
        r_override = min(1.0, max(0.0, data.reviewer_overrides / data.total_findings))
    else:
        r_override = 0.0

    # 3. Reviewer Disagreement Rate
    rev_total = data.reviewer_acceptances + data.reviewer_dismissals
    if rev_total >= 2:
        # Gini-based normalized discordance: 4 * P(accept) * P(dismiss)
        p_acc = data.reviewer_acceptances / rev_total
        p_dis = data.reviewer_dismissals / rev_total
        r_disagree = min(1.0, max(0.0, 4.0 * p_acc * p_dis))
    else:
        r_disagree = 0.0

    # 4. Clarification Rate
    denom = max(1, data.total_findings)
    r_clarify = min(1.0, max(0.0, data.clarification_comments / denom))

    # Weighted sum
    raw_score = 30.0 * r_dismiss + 30.0 * r_override + 25.0 * r_disagree + 15.0 * r_clarify
    ambiguity_score = int(round(min(100.0, max(0.0, raw_score))))

    # Recommendation heuristic
    if ambiguity_score >= 60:
        recommendation = "High ambiguity: Rule wording requires urgent brand manager revision or clearer exception criteria."
    elif ambiguity_score >= 35:
        recommendation = "Moderate ambiguity: Periodic overrides observed; consider adding positive/negative examples."
    else:
        recommendation = "Stable: High compliance consensus with low reviewer friction."

    return AmbiguityResult(
        rule_code=data.rule_code,
        rule_title=data.rule_title,
        rule_type=data.rule_type,
        total_events=total_events,
        times_triggered=data.total_findings,
        creator_dismissals=data.creator_dismissals,
        reviewer_overrides=data.reviewer_overrides,
        clarification_comments=data.clarification_comments,
        dismissal_rate=round(r_dismiss, 3),
        override_rate=round(r_override, 3),
        disagreement_rate=round(r_disagree, 3),
        clarification_rate=round(r_clarify, 3),
        ambiguity_score=ambiguity_score,
        status="evaluated",
        recommendation=recommendation,
    )
