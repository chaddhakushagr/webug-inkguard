"""
Pure domain utility for computing diffs between content versions.
Zero external dependencies.
"""

import difflib
from typing import Dict, Any


def compute_content_diff(text1: str, text2: str, v1: int = 1, v2: int = 2) -> Dict[str, Any]:
    """Computes unified diff between two text versions."""
    lines1 = text1.splitlines(keepends=True)
    lines2 = text2.splitlines(keepends=True)

    diff = list(
        difflib.unified_diff(
            lines1,
            lines2,
            fromfile=f"version_{v1}",
            tofile=f"version_{v2}",
            n=3,
        )
    )

    diff_text = "".join(diff)

    added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

    return {
        "from_version": v1,
        "to_version": v2,
        "diff_text": diff_text or "No differences between versions.",
        "added_lines": added,
        "removed_lines": removed,
    }
