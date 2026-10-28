"""
Cached LLM adapter wrapping any LLMPort implementation.
Keys cache entries by content hash, KB snapshot hash, prompt version, and model id.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.ports.llm import LLMPort


def generate_cache_key(
    content: str,
    kb_entries: List[Dict[str, Any]],
    prompt_version: str,
    model: str,
) -> str:
    kb_summary = sorted([e.get("code", "") for e in kb_entries])
    raw = f"{content.strip()}|{','.join(kb_summary)}|{prompt_version}|{model}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class CachedLLMAdapter:
    """Caching wrapper for LLM adapters."""

    def __init__(self, inner_adapter: LLMPort, cache_store: Optional[Dict[str, Any]] = None):
        self.inner = inner_adapter
        self.cache: Dict[str, Any] = cache_store if cache_store is not None else {}
        self.last_cache_hit: bool = False

    def analyze(
        self,
        sanitised_text: str,
        kb_entries: List[Dict[str, Any]],
        channel: str = "social",
        prompt_version: str = "v1",
    ) -> Dict[str, Any]:
        model = getattr(self.inner, "model", "mock")
        key = generate_cache_key(sanitised_text, kb_entries, prompt_version, model)

        if key in self.cache:
            self.last_cache_hit = True
            return self.cache[key]

        # Check disk cache in eval/cache first, then seed/cache
        import os
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cache_dirs = [
            os.path.join(base_dir, "eval", "cache"),
            os.path.join(base_dir, "seed", "cache"),
        ]

        for c_dir in cache_dirs:
            disk_file = os.path.join(c_dir, f"{key}.json")
            if os.path.exists(disk_file):
                try:
                    with open(disk_file, "r", encoding="utf-8") as f:
                        cached_data = json.load(f)
                        self.cache[key] = cached_data
                        self.last_cache_hit = True
                        return cached_data
                except Exception:
                    pass

        self.last_cache_hit = False
        res = self.inner.analyze(sanitised_text, kb_entries, channel=channel, prompt_version=prompt_version)
        self.cache[key] = res

        # Persist to disk cache (both eval/cache and seed/cache)
        for c_dir in cache_dirs:
            os.makedirs(c_dir, exist_ok=True)
            disk_file = os.path.join(c_dir, f"{key}.json")
            try:
                with open(disk_file, "w", encoding="utf-8") as f:
                    json.dump(res, f, indent=2)
            except Exception:
                pass

        return res

    def suggest_fixes(
        self,
        sanitised_text: str,
        findings: List[Dict[str, Any]],
        kb_entries: List[Dict[str, Any]],
        prompt_version: str = "v1",
    ) -> List[Dict[str, Any]]:
        return self.inner.suggest_fixes(sanitised_text, findings, kb_entries, prompt_version=prompt_version)

    def verify(
        self,
        finding: Dict[str, Any],
        excerpt: str,
        cited_entry: Dict[str, Any],
        prompt_version: str = "v1",
    ) -> Dict[str, Any]:
        model = getattr(self.inner, "model", "mock")
        raw = f"{finding.get('issue_type')}|{finding.get('explanation')}|{excerpt.strip()}|{cited_entry.get('code')}|{prompt_version}|{model}"
        key = "vfy_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()

        if key in self.cache:
            self.last_cache_hit = True
            return self.cache[key]

        import os
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cache_dirs = [
            os.path.join(base_dir, "eval", "cache"),
            os.path.join(base_dir, "seed", "cache"),
        ]

        for c_dir in cache_dirs:
            disk_file = os.path.join(c_dir, f"{key}.json")
            if os.path.exists(disk_file):
                try:
                    with open(disk_file, "r", encoding="utf-8") as f:
                        cached_data = json.load(f)
                        self.cache[key] = cached_data
                        self.last_cache_hit = True
                        return cached_data
                except Exception:
                    pass

        self.last_cache_hit = False
        res = self.inner.verify(finding, excerpt, cited_entry, prompt_version=prompt_version)
        self.cache[key] = res

        # Persist to disk cache (both eval/cache and seed/cache)
        for c_dir in cache_dirs:
            os.makedirs(c_dir, exist_ok=True)
            disk_file = os.path.join(c_dir, f"{key}.json")
            try:
                with open(disk_file, "w", encoding="utf-8") as f:
                    json.dump(res, f, indent=2)
            except Exception:
                pass

        return res
