"""
Pure Python domain module for Comment Gap Detection (Round 3 Improvement 2).
Clusters uncited reviewer comments using BM25 lexical similarity (zero external ML).
Generates deterministic draft KB entries for approved human review.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Set, Tuple, Optional
import math
import re
import uuid


STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can", "can't", "cannot", "could", "did", "do", "does", "doing", "don't", "down", "during", "each",
    "few", "for", "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "isn't", "it", "its", "itself", "let's",
    "me", "more", "most", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or",
    "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "she", "should", "so",
    "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then", "there", "these",
    "they", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we",
    "were", "weren't", "what", "when", "where", "which", "while", "who", "whom", "why", "with", "won't",
    "would", "you", "your", "yours", "yourself", "yourselves", "please", "needs", "need", "must", "should",
    "add", "make", "sure", "ensure"
}


def tokenize(text: str) -> List[str]:
    """Tokenizes text into lowercase terms, discarding stop words and single chars."""
    if not text:
        return []
    words = re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", text.lower())
    return [w for w in words if w not in STOP_WORDS]


@dataclass(frozen=True)
class CommentItem:
    id: str
    body: str
    author_id: str
    submission_id: str
    created_at: Optional[datetime] = None


@dataclass(frozen=True)
class DraftKBEntryProposal:
    id: str
    code: str
    title: str
    type: str  # "rule"
    body: str
    classification: str  # "internal"
    status: str  # "draft"
    cluster_size: int
    top_keywords: List[str]
    sample_comments: List[str]
    created_at: str


def compute_bm25_pairwise_similarity(
    tokens_a: List[str],
    tokens_b: List[str],
    doc_freqs: Dict[str, int],
    total_docs: int,
    avg_len: float,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """Computes BM25 score of tokens_a querying tokens_b."""
    if not tokens_a or not tokens_b:
        return 0.0

    b_len = len(tokens_b)
    b_term_freqs: Dict[str, int] = {}
    for t in tokens_b:
        b_term_freqs[t] = b_term_freqs.get(t, 0) + 1

    score = 0.0
    for t in set(tokens_a):
        if t in doc_freqs and t in b_term_freqs:
            df = doc_freqs[t]
            idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1.0)
            tf = b_term_freqs[t]
            numerator = tf * (k1 + 1.0)
            denominator = tf + k1 * (1.0 - b + b * (b_len / max(1.0, avg_len)))
            score += idf * (numerator / max(0.001, denominator))

    return score


def cluster_uncited_comments(
    comments: List[CommentItem],
    min_cluster_size: int = 2,
    similarity_threshold: float = 0.25,
) -> List[DraftKBEntryProposal]:
    """
    Clusters uncited reviewer comments by lexical BM25 similarity.
    Pure Python agglomerative clustering with zero external ML dependencies.
    Produces deterministic draft KB entries for valid clusters.
    """
    if len(comments) < min_cluster_size:
        return []

    # 1. Tokenize comments
    tokenized_comments: List[List[str]] = [tokenize(c.body) for c in comments]

    # Compute global document frequencies
    total_docs = len(comments)
    doc_freqs: Dict[str, int] = {}
    for doc in tokenized_comments:
        for t in set(doc):
            doc_freqs[t] = doc_freqs.get(t, 0) + 1

    avg_len = sum(len(d) for d in tokenized_comments) / max(1.0, total_docs)

    # 2. Pairwise similarity matrix with cosine normalization
    self_scores: List[float] = []
    for doc in tokenized_comments:
        s = compute_bm25_pairwise_similarity(doc, doc, doc_freqs, total_docs, avg_len)
        self_scores.append(max(0.001, s))

    # Build adjacency graph
    adj: Dict[int, Set[int]] = {i: {i} for i in range(total_docs)}

    for i in range(total_docs):
        for j in range(i + 1, total_docs):
            if not tokenized_comments[i] or not tokenized_comments[j]:
                continue
            overlap = set(tokenized_comments[i]) & set(tokenized_comments[j])
            if not overlap:
                continue

            shared_idf = sum(math.log((total_docs - doc_freqs.get(t, 1) + 0.5) / (doc_freqs.get(t, 1) + 0.5) + 1.0) for t in overlap)
            total_idf = sum(math.log((total_docs - doc_freqs.get(t, 1) + 0.5) / (doc_freqs.get(t, 1) + 0.5) + 1.0) for t in (set(tokenized_comments[i]) | set(tokenized_comments[j])))
            weighted_jaccard = shared_idf / max(0.001, total_idf)

            s_ij = compute_bm25_pairwise_similarity(tokenized_comments[i], tokenized_comments[j], doc_freqs, total_docs, avg_len)
            s_ji = compute_bm25_pairwise_similarity(tokenized_comments[j], tokenized_comments[i], doc_freqs, total_docs, avg_len)
            avg_score = (s_ij + s_ji) / 2.0
            bm25_norm = avg_score / math.sqrt(self_scores[i] * self_scores[j])
            norm_sim = max(weighted_jaccard, bm25_norm)

            if norm_sim >= similarity_threshold:
                adj[i].add(j)
                adj[j].add(i)

    # 3. Connected components (clusters)
    visited: Set[int] = set()
    raw_clusters: List[List[int]] = []

    for i in range(total_docs):
        if i not in visited:
            component = []
            queue = [i]
            visited.add(i)
            while queue:
                curr = queue.pop(0)
                component.append(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            if len(component) >= min_cluster_size:
                raw_clusters.append(component)

    # Sort clusters by size descending
    raw_clusters.sort(key=lambda c: len(c), reverse=True)

    # 4. Generate deterministic draft KB entries
    proposals: List[DraftKBEntryProposal] = []

    for idx, cluster in enumerate(raw_clusters, start=1):
        cluster_comments = [comments[i] for i in cluster]
        sorted_comment_ids = sorted([c.id for c in cluster_comments])
        cluster_seed_str = "-".join(sorted_comment_ids)
        deterministic_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"inkguard-gap-cluster-{cluster_seed_str}"))

        # Find most frequent keywords in this cluster
        term_counts: Dict[str, int] = {}
        for i in cluster:
            for t in tokenized_comments[i]:
                term_counts[t] = term_counts.get(t, 0) + 1

        # Rank keywords by frequency * IDF
        keyword_scores: List[Tuple[str, float]] = []
        for t, cnt in term_counts.items():
            df = doc_freqs.get(t, 1)
            idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1.0)
            keyword_scores.append((t, cnt * idf))

        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        top_terms = [t for t, _ in keyword_scores[:4]]
        topic_header = " & ".join(t.capitalize() for t in top_terms[:2]) if top_terms else "Governance Standard"

        code = f"RULE-GAP-{idx:02d}"
        title = f"Reviewer Gap: {topic_header} Requirements"

        sample_texts = [c.body.strip() for c in cluster_comments[:4]]
        formatted_samples = "\n".join(f"- \"{txt}\"" for txt in sample_texts)

        body = (
            f"Policy Gap identified from {len(cluster)} reviewer change-request comments citing no active rule.\n\n"
            f"Key Reviewer Feedback:\n{formatted_samples}\n\n"
            f"Prescribed Standard:\nMarketing and copy teams must ensure compliance with {topic_header.lower()} "
            f"guidance prior to publication."
        )

        proposals.append(
            DraftKBEntryProposal(
                id=deterministic_uuid,
                code=code,
                title=title,
                type="rule",
                body=body,
                classification="internal",
                status="draft",
                cluster_size=len(cluster),
                top_keywords=top_terms,
                sample_comments=sample_texts,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
        )

    return proposals
