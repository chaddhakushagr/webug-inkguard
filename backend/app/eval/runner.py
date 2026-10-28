"""
Evaluation runner for Inkguard.
Executes the brand governance review pipeline on benchmark documents,
supports rules_only, mock, cached, and live modes, respects LLM_DAILY_CAP,
caches live responses for replayability, and generates detailed reports.
"""

import os
import sys
import json
import time
from typing import List, Dict, Any, Optional

from app.config import settings
from app.eval.schema import EvalDocument
from app.eval.metrics import compute_eval_metrics, EvalReport
from app.domain.review.models import ReviewContext, FindingItem
from app.domain.review.pipeline import (
    ExtractStage,
    RetrieveStage,
    AnalyseStage,
    ConfidenceFilterStage,
    GuardrailsStage,
)
from app.domain.review.verifier import LLMVerifierStage
from app.domain.review.sanitise import SanitiseStage
from app.domain.review.rule_engine import RuleChecksStage
from app.domain.review.accessibility import A11yChecksStage
from app.adapters.retrieval.bm25 import BM25Retriever
from app.adapters.llm.mock import MockLLMAdapter
from app.adapters.llm.cached import CachedLLMAdapter, generate_cache_key
from app.seed.lumo_brand import (
    SEED_TERMS,
    SEED_RULES,
    SEED_FACTS,
    SEED_TONE,
    SEED_ASSETS,
)


CACHE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "cache")
)


class EvalRunner:
    """Orchestrates evaluation runs over EvalDocuments."""

    def __init__(
        self,
        mode: str = "rules_only",
        verifier_enabled: bool = False,
        daily_cap: Optional[int] = None,
        claim_confidence_threshold: Optional[float] = None,
    ):
        self.mode = mode.lower()
        self.verifier_enabled = verifier_enabled
        self.daily_cap = daily_cap if daily_cap is not None else settings.LLM_DAILY_CAP
        self.claim_confidence_threshold = (
            claim_confidence_threshold
            if claim_confidence_threshold is not None
            else settings.CLAIM_CONFIDENCE_THRESHOLD
        )
        self.retriever = BM25Retriever()
        self.kb_pool = SEED_TERMS + SEED_RULES + SEED_FACTS + SEED_TONE + SEED_ASSETS
        self.live_calls_made = 0
        self.llm_adapter = self._init_llm_adapter()

        os.makedirs(CACHE_DIR, exist_ok=True)

    def _init_llm_adapter(self):
        if self.mode == "rules_only":
            return None

        if self.mode == "mock":
            return MockLLMAdapter()

        # For cached or live
        from app.adapters.llm.openai_compatible import OpenAICompatibleLLMAdapter

        if self.mode == "live":
            # Live uses cached adapter wrapping live OpenAI-compatible adapter
            # to record results for resumability
            inner = OpenAICompatibleLLMAdapter()
            return CachedLLMAdapter(inner)

        if self.mode == "cached":
            # In cached mode, prefer live adapter wrapped in cache if key is set,
            # otherwise fall back to Mock wrapped in cache
            if settings.LLM_API_KEY:
                try:
                    inner = OpenAICompatibleLLMAdapter()
                    return CachedLLMAdapter(inner)
                except Exception:
                    pass
            return CachedLLMAdapter(MockLLMAdapter())

        return MockLLMAdapter()

    def run_document(self, doc: EvalDocument) -> List[Dict[str, Any]]:
        """Runs the review pipeline on a single document and returns predicted findings."""
        effective_mode = self.mode
        if effective_mode == "live" and self.live_calls_made >= self.daily_cap:
            effective_mode = "rules_only"

        # Check if already cached when in live/cached mode
        if effective_mode == "live" and self.llm_adapter:
            key = generate_cache_key(
                doc.text,
                self.kb_pool,
                "v1",
                getattr(self.llm_adapter, "model", settings.LLM_MODEL),
            )
            disk_file = os.path.join(CACHE_DIR, f"{key}.json")
            if not os.path.exists(disk_file):
                # Call will be made to external API
                self.live_calls_made += 1

        context = ReviewContext(
            text=doc.text,
            channel=doc.channel,
            user_max_tier="confidential",
            kb_pool=self.kb_pool,
            mode="rules_only" if effective_mode == "rules_only" else "mock" if effective_mode == "mock" else "live",
            metadata={"doc_id": doc.id},
        )

        # Stage 1: Extract & Sanitise
        context = ExtractStage().process(context)
        context = SanitiseStage().process(context)

        # Stage 2: Rule Checks & Accessibility Checks
        context = RuleChecksStage().process(context)
        context = A11yChecksStage().process(context)

        # Stage 3: Retrieval
        context = RetrieveStage(self.retriever).process(context)

        # Stage 4: LLM Analysis
        if context.mode != "rules_only" and self.llm_adapter:
            try:
                context = AnalyseStage(self.llm_adapter).process(context)
            except Exception as e:
                # Fallback gracefully
                context.stats["llm_error"] = str(e)

        # Stage 4b: Filter low-confidence AI claim and tone findings before guardrails
        context = ConfidenceFilterStage(threshold=self.claim_confidence_threshold).process(context)

        # Stage 5: Guardrails
        context = GuardrailsStage().process(context)

        # Stage 6: Secondary LLM Verifier Pass (if enabled)
        if self.verifier_enabled:
            context = LLMVerifierStage(llm_adapter=self.llm_adapter, enabled=True).process(context)

        return [f.to_dict() for f in context.findings]

    def evaluate(
        self,
        docs: List[EvalDocument],
        limit: Optional[int] = None,
        require_verdict_match: bool = False,
    ) -> EvalReport:
        """Evaluates a list of documents and returns an EvalReport."""
        target_docs = docs[:limit] if limit else docs
        predictions: Dict[str, List[Dict[str, Any]]] = {}

        for doc in target_docs:
            findings = self.run_document(doc)
            predictions[doc.id] = findings

        return compute_eval_metrics(
            target_docs,
            predictions,
            require_verdict_match=require_verdict_match,
        )


def format_report_table(report: EvalReport, mode: str, verifier: bool) -> str:
    """Formats an evaluation report as a clean Markdown table."""
    s = report.to_dict()["summary"]
    ov = s["overall"]

    lines = [
        f"\n### Evaluation Results: Mode `{mode}` (Verifier: {'ON' if verifier else 'OFF'})",
        f"- **Total Documents**: {s['total_documents']} | **Clean Documents**: {s['clean_documents']} (Clean Pass Rate: {s['clean_pass_rate']:.1%})",
        f"- **Overall**: Precision: **{ov['precision']:.3f}** | Recall: **{ov['recall']:.3f}** | F1: **{ov['f1']:.3f}** (TP: {ov['tp']}, FP: {ov['fp']}, FN: {ov['fn']})\n",
        "| Category | TP | FP | FN | Precision | Recall | F1 |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for itype, m in sorted(report.by_issue_type.items()):
        lines.append(
            f"| `{itype}` | {m.true_positives} | {m.false_positives} | {m.false_negatives} | {m.precision:.3f} | {m.recall:.3f} | {m.f1:.3f} |"
        )

    if report.by_claim_verdict:
        lines.append("\n**Claim Verdict Breakdown**:\n")
        lines.append("| Verdict | TP | FP | FN | Precision | Recall | F1 |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
        for verd, m in sorted(report.by_claim_verdict.items()):
            lines.append(
                f"| `{verd}` | {m.true_positives} | {m.false_positives} | {m.false_negatives} | {m.precision:.3f} | {m.recall:.3f} | {m.f1:.3f} |"
            )

    return "\n".join(lines)
