"""
Pure domain review models, stage protocol, and review context.
Zero external framework or database dependencies.
"""

from typing import List, Dict, Any, Optional, Protocol
from dataclasses import dataclass, field


@dataclass
class FindingItem:
    id: str
    source: str  # "rule" or "ai"
    issue_type: str  # terminology, tone, claim, missing_disclaimer, confidential_leak, accessibility, readability, general_note
    severity: str  # "low", "medium", "high"
    confidence: float
    span_start: int
    span_end: int
    excerpt: str
    explanation: str
    suggested_fix: Optional[str] = None
    cited_entry_code: Optional[str] = None
    cited_entry_id: Optional[str] = None
    cited_entry_version: Optional[int] = None
    claim_verdict: Optional[str] = None  # Supported, Contradicted, Unverified, Expired
    is_policy: bool = True
    needs_human_judgment: bool = False
    fingerprint: Optional[str] = None
    verifier_verdict: Optional[str] = None  # supported, not_supported, unsure
    verifier_reason: Optional[str] = None
    location: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "issue_type": self.issue_type,
            "severity": self.severity,
            "confidence": self.confidence,
            "span_start": self.span_start,
            "span_end": self.span_end,
            "excerpt": self.excerpt,
            "explanation": self.explanation,
            "suggested_fix": self.suggested_fix,
            "cited_entry_code": self.cited_entry_code,
            "cited_entry_id": self.cited_entry_id,
            "cited_entry_version": self.cited_entry_version,
            "claim_verdict": self.claim_verdict,
            "is_policy": self.is_policy,
            "needs_human_judgment": self.needs_human_judgment,
            "fingerprint": self.fingerprint,
            "verifier_verdict": self.verifier_verdict,
            "verifier_reason": self.verifier_reason,
            "location": self.location,
        }


@dataclass
class ReviewContext:
    text: str
    channel: str = "social"
    user_max_tier: str = "internal"
    sanitised_text: str = ""
    placeholder_map: Dict[str, str] = field(default_factory=dict)
    redaction_log: Dict[str, int] = field(default_factory=lambda: {"emails": 0, "phones": 0, "api_keys": 0, "secrets": 0})
    flags: List[str] = field(default_factory=list)
    kb_pool: List[Dict[str, Any]] = field(default_factory=list)
    kb_retrieved: List[Dict[str, Any]] = field(default_factory=list)
    findings: List[FindingItem] = field(default_factory=list)
    mode: str = "mock"
    stats: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    document_structure: Optional[Any] = None


class ReviewStage(Protocol):
    """Protocol for an ordered stage in the review pipeline."""
    name: str

    def process(self, context: ReviewContext) -> ReviewContext:
        ...
