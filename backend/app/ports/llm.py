from typing import Protocol, List, Dict, Any, Optional


class LLMPort(Protocol):
    """Port interface for LLM provider adapters."""

    def analyze(
        self,
        sanitised_text: str,
        kb_entries: List[Dict[str, Any]],
        channel: str = "social",
        prompt_version: str = "v1",
    ) -> Dict[str, Any]:
        """
        Executes policy and claim analysis over sanitised text.
        Returns strict JSON dictionary: {"claims": [...], "tone": [...], "notes": [...]}.
        """
        ...

    def suggest_fixes(
        self,
        sanitised_text: str,
        findings: List[Dict[str, Any]],
        kb_entries: List[Dict[str, Any]],
        prompt_version: str = "v1",
    ) -> List[Dict[str, Any]]:
        """
        Generates minimal-edit suggestion replacements for reported findings.
        """
        ...
