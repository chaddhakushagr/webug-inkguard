"""
LLM adapter package with factory function for mock, live, cached, and rules_only.
"""

from typing import Optional
from app.ports.llm import LLMPort
from app.adapters.llm.mock import MockLLMAdapter
from app.adapters.llm.openai_compatible import OpenAICompatibleLLMAdapter
from app.adapters.llm.cached import CachedLLMAdapter
from app.config import settings

_global_cache: dict = {}


def get_llm_adapter(mode: Optional[str] = None) -> LLMPort:
    """
    Factory creating configured LLM adapter according to mode:
    - mock: deterministic fixture adapter (offline default)
    - cached: caching wrapper over live (or mock if no key)
    - live: direct OpenAI-compatible HTTP adapter
    - rules_only: mock adapter configured to skip external LLM calls
    """
    target_mode = (mode or settings.LLM_MODE).lower()

    if target_mode == "mock":
        return MockLLMAdapter()
    elif target_mode == "cached":
        inner = OpenAICompatibleLLMAdapter() if settings.LLM_API_KEY else MockLLMAdapter()
        return CachedLLMAdapter(inner_adapter=inner, cache_store=_global_cache)
    elif target_mode == "live":
        return OpenAICompatibleLLMAdapter()
    elif target_mode == "rules_only":
        return MockLLMAdapter()

    return MockLLMAdapter()


__all__ = [
    "MockLLMAdapter",
    "OpenAICompatibleLLMAdapter",
    "CachedLLMAdapter",
    "get_llm_adapter",
]
