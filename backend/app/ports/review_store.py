"""
Port interface for review persistence and store operations.
Clean architecture protocol implemented by adapters/db/review_store.py.
Zero external framework dependencies.
"""

from typing import Protocol, List, Dict, Any, Optional


class ReviewStorePort(Protocol):
    """Protocol for review persistence and data boundary telemetry."""

    def get_submission_context(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """Fetch submission metadata, current content, channel, version_id, creator_id."""
        ...

    def get_kb_pool(self, user_max_tier: str) -> List[Dict[str, Any]]:
        """Fetch active KB entries up to the specified user tier."""
        ...

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Fetch a system setting value (e.g. no_external_ai, llm_daily_cap)."""
        ...

    def get_daily_live_calls_count(self) -> int:
        """Count live external AI calls executed today."""
        ...

    def update_review_progress(self, review_id: str, status: str, error: Optional[str] = None) -> None:
        """Update review progress state (extracting, rule_checks, retrieving, analysing, finalising)."""
        ...

    def save_review_results(
        self,
        review_id: str,
        submission_id: str,
        submission_version_id: str,
        findings: List[Dict[str, Any]],
        stats: Dict[str, Any],
        mode: str,
        provider: str,
        model: str,
        ai_call_data: Optional[Dict[str, Any]] = None,
        fallback_reason: Optional[str] = None,
        actor_id: Optional[str] = None,
        actor_role: Optional[str] = None,
    ) -> None:
        """
        Persist findings, ai_calls record, mark review completed,
        transition submission to Checked, and append cryptographic audit row.
        """
        ...

    def fail_review(self, review_id: str, error: str) -> None:
        """Mark review as failed with error message."""
        ...
