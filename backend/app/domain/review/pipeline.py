"""
Pure domain review pipeline runner.
Chains Extract, Sanitise, RuleChecks, A11yChecks, Retrieve, Analyse, Guardrails, and Suggest.
Zero web, database or HTTP framework dependencies.
"""

import time
import re
from typing import List, Dict, Any, Optional
from app.domain.review.models import ReviewContext, FindingItem, ReviewStage
from app.domain.review.sanitise import SanitiseStage
from app.domain.review.rule_engine import RuleChecksStage
from app.domain.review.accessibility import A11yChecksStage
from app.domain.review.guardrails import GuardrailsStage
from app.domain.review.suggestion_validator import SuggestionValidatorStage
from app.ports.retrieval import RetrieverPort
from app.ports.llm import LLMPort


class ExtractStage:
    name: str = "Extract"

    def process(self, context: ReviewContext) -> ReviewContext:
        # Normalize whitespace while maintaining original string length and line structures
        text = context.text.replace("\r\n", "\n")
        context.text = text
        context.sanitised_text = text
        return context


class RetrieveStage:
    name: str = "Retrieve"

    def __init__(self, retriever: RetrieverPort):
        self.retriever = retriever

    def process(self, context: ReviewContext) -> ReviewContext:
        query = context.text
        # Retrieve top tone, facts, rules up to user's max tier
        retrieved = self.retriever.retrieve(
            query=query,
            kb_pool=context.kb_pool,
            user_max_tier=context.user_max_tier,
            limit=15,
        )
        context.kb_retrieved = retrieved
        return context


class AnalyseStage:
    name: str = "Analyse"

    def __init__(self, llm_adapter: LLMPort):
        self.llm = llm_adapter

    def process(self, context: ReviewContext) -> ReviewContext:
        # Only run LLM analysis if mode is not rules_only
        if context.mode == "rules_only":
            return context

        analysis_result = self.llm.analyze(
            sanitised_text=context.sanitised_text,
            kb_entries=context.kb_retrieved,
            channel=context.channel,
        )

        seq = len(context.findings) + 1
        claims = analysis_result.get("claims", [])
        tone = analysis_result.get("tone", [])
        notes = analysis_result.get("notes", [])

        # Process claims
        for c in claims:
            excerpt = c.get("excerpt", "").strip()
            if not excerpt:
                continue

            # Compute initial span in original text
            idx = context.text.find(excerpt)
            start = idx if idx != -1 else 0
            end = start + len(excerpt)

            context.findings.append(
                FindingItem(
                    id=f"find-ai-{seq:03d}",
                    source="ai",
                    issue_type="claim",
                    severity="high" if c.get("verdict") == "Contradicted" else "medium",
                    confidence=float(c.get("confidence", 0.85)),
                    span_start=start,
                    span_end=end,
                    excerpt=excerpt,
                    explanation=c.get("explanation", c.get("claim_text", "Claim analysis")),
                    cited_entry_code=c.get("cited_entry_code"),
                    claim_verdict=c.get("verdict", "Unverified"),
                    is_policy=True,
                )
            )
            seq += 1

        # Process tone findings
        for t in tone:
            excerpt = t.get("excerpt", "").strip()
            if not excerpt or t.get("assessment") == "compliant":
                continue

            idx = context.text.find(excerpt)
            start = idx if idx != -1 else 0
            end = start + len(excerpt)

            context.findings.append(
                FindingItem(
                    id=f"find-ai-{seq:03d}",
                    source="ai",
                    issue_type="tone",
                    severity="medium",
                    confidence=float(t.get("confidence", 0.85)),
                    span_start=start,
                    span_end=end,
                    excerpt=excerpt,
                    explanation=t.get("explanation", "Tone guideline deviation"),
                    cited_entry_code=t.get("cited_entry_code") or t.get("attribute_code"),
                    is_policy=True,
                )
            )
            seq += 1

        # Process notes
        for n in notes:
            excerpt = n.get("excerpt", "").strip()
            context.findings.append(
                FindingItem(
                    id=f"find-ai-{seq:03d}",
                    source="ai",
                    issue_type="general_note",
                    severity="low",
                    confidence=0.75,
                    span_start=0,
                    span_end=min(len(context.text), len(excerpt) if excerpt else 10),
                    excerpt=excerpt or context.text[:20],
                    explanation=n.get("note", "General observation"),
                    is_policy=False,
                )
            )
            seq += 1

        return context


class ReviewPipeline:
    """Orchestrates ordered stages over ReviewContext."""

    def __init__(self, retriever: RetrieverPort, llm_adapter: LLMPort):
        self.retriever = retriever
        self.llm = llm_adapter

        self.stages: List[ReviewStage] = [
            ExtractStage(),
            SanitiseStage(),
            RuleChecksStage(),
            A11yChecksStage(),
            RetrieveStage(self.retriever),
            AnalyseStage(self.llm),
            GuardrailsStage(),
            SuggestionValidatorStage(),
        ]

    def run(self, context: ReviewContext) -> ReviewContext:
        start_time = time.perf_counter()

        for stage in self.stages:
            context = stage.process(context)

        # Run minimal-edit suggestions if LLM is active and suggestions absent
        if context.mode != "rules_only":
            findings_dicts = [f.to_dict() for f in context.findings if not f.suggested_fix]
            if findings_dicts:
                sugg_list = self.llm.suggest_fixes(
                    sanitised_text=context.sanitised_text,
                    findings=findings_dicts,
                    kb_entries=context.kb_retrieved,
                )
                sugg_map = {s["finding_id"]: s["suggested_fix"] for s in sugg_list if "finding_id" in s}
                for f in context.findings:
                    if f.id in sugg_map:
                        f.suggested_fix = sugg_map[f.id]

                # Re-validate generated suggestions
                context = SuggestionValidatorStage().process(context)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        context.stats = {
            "rules_evaluated": len(context.kb_pool),
            "kb_retrieved_count": len(context.kb_retrieved),
            "findings_count": len(context.findings),
            "latency_ms": elapsed_ms,
        }

        return context
