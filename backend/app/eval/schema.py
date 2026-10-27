"""
Data models and schema validation for evaluation benchmark documents.
Pure Python dataclasses with JSON serialization support.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class ExpectedFinding:
    """A hand-labeled ground-truth policy finding for evaluation."""
    entry_code: str
    span_start: int
    span_end: int
    excerpt: str
    issue_type: str
    verdict: Optional[str] = None
    severity: Optional[str] = "medium"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExpectedFinding":
        return cls(
            entry_code=str(data["entry_code"]).strip(),
            span_start=int(data["span_start"]),
            span_end=int(data["span_end"]),
            excerpt=str(data["excerpt"]),
            issue_type=str(data["issue_type"]).strip(),
            verdict=data.get("verdict"),
            severity=data.get("severity", "medium"),
        )


@dataclass
class EvalDocument:
    """A benchmark marketing copy document with ground-truth expected findings."""
    id: str
    channel: str
    title: str
    text: str
    expected_findings: List[ExpectedFinding] = field(default_factory=list)
    notes: Optional[str] = None

    @property
    def is_clean(self) -> bool:
        """A clean document has zero expected policy violations."""
        return len(self.expected_findings) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "channel": self.channel,
            "title": self.title,
            "text": self.text,
            "expected_findings": [f.to_dict() for f in self.expected_findings],
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvalDocument":
        findings = [
            ExpectedFinding.from_dict(f) for f in data.get("expected_findings", [])
        ]
        return cls(
            id=str(data["id"]).strip(),
            channel=str(data.get("channel", "social")).strip().lower(),
            title=str(data.get("title", "")).strip(),
            text=str(data.get("text", "")),
            expected_findings=findings,
            notes=data.get("notes"),
        )
