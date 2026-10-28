"""
Domain insights package for Guideline Health Intelligence (Round 3 Improvement 2).
Pure Python logic for ambiguity scoring, stale rule detection, and comment gap clustering.
"""

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
)

__all__ = [
    "AmbiguityInput",
    "AmbiguityResult",
    "compute_ambiguity_score",
    "is_clarification_comment",
    "StaleRuleItem",
    "detect_stale_rules",
    "CommentItem",
    "DraftKBEntryProposal",
    "cluster_uncited_comments",
]
