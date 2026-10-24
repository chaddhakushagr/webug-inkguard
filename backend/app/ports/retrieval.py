from typing import Protocol, List, Dict, Any


class RetrieverPort(Protocol):
    """Port interface for knowledge base retrieval."""

    def retrieve(
        self,
        query: str,
        kb_pool: List[Dict[str, Any]],
        user_max_tier: str = "internal",
        limit: int = 15,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves relevant knowledge base entries scored against the query.
        Entries above user_max_tier or classified as confidential are excluded.
        """
        ...
