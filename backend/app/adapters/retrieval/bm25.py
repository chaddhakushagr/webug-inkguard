"""
In-process BM25 lexical retriever adapter.
Ranks knowledge base facts, terms, tone, and rules against query text.
Enforces classification tier ceiling and confidential egress exclusion.
"""

import math
import re
from typing import List, Dict, Any, Set
from app.domain.workflow.permissions import can_access_tier
from app.ports.retrieval import RetrieverPort


def tokenize(text: str) -> List[str]:
    return [w.lower() for w in re.findall(r"\b\w{2,}\b", text)]


class BM25Retriever:
    """In-process BM25 lexical retriever implementing RetrieverPort."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def retrieve(
        self,
        query: str,
        kb_pool: List[Dict[str, Any]],
        user_max_tier: str = "internal",
        limit: int = 15,
    ) -> List[Dict[str, Any]]:
        # 1. Tier filtering and confidential egress boundary
        eligible_entries = []
        for entry in kb_pool:
            classification = entry.get("classification", "internal").lower()
            # Confidential entries are strictly excluded from retrieval egress
            if classification == "confidential":
                continue
            if can_access_tier(user_max_tier, classification):
                eligible_entries.append(entry)

        if not eligible_entries:
            return []

        # 2. Build corpus documents
        docs = []
        for e in eligible_entries:
            data = e.get("data") or {}
            doc_text = f"{e.get('title', '')} {e.get('body', '')} {data.get('statement', '')} {data.get('banned', '')} {data.get('preferred', '')} {data.get('attribute', '')}"
            docs.append(tokenize(doc_text))

        query_tokens = tokenize(query)
        if not query_tokens:
            return eligible_entries[:limit]

        # 3. BM25 calculation
        doc_count = len(docs)
        avg_doc_len = sum(len(d) for d in docs) / max(1, doc_count)

        # IDF calculation
        df: Dict[str, int] = {}
        for d in docs:
            for term in set(d):
                df[term] = df.get(term, 0) + 1

        scores = []
        for i, doc in enumerate(docs):
            score = 0.0
            doc_len = len(doc)
            term_freqs: Dict[str, int] = {}
            for t in doc:
                term_freqs[t] = term_freqs.get(t, 0) + 1

            for token in query_tokens:
                if token in df:
                    n = df[token]
                    idf = math.log((doc_count - n + 0.5) / (n + 0.5) + 1.0)
                    tf = term_freqs.get(token, 0)
                    numerator = tf * (self.k1 + 1.0)
                    denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / max(1.0, avg_doc_len)))
                    score += idf * (numerator / max(0.001, denominator))

            # Bonus for exact code mention in query
            code = eligible_entries[i].get("code", "")
            if code and code.lower() in query.lower():
                score += 10.0

            scores.append((score, eligible_entries[i]))

        # Sort by score descending
        scores.sort(key=lambda x: x[0], reverse=True)

        # Return entries with positive score, or top pool if query terms generic
        results = [entry for score, entry in scores if score > 0.0]
        if not results:
            results = [entry for _, entry in scores]

        return results[:limit]
