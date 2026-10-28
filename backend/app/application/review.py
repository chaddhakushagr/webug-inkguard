"""
Review Orchestrator Application Use Case.
Orchestrates the 7-stage domain review pipeline in background execution,
records progress states (extracting, rule_checks, retrieving, analysing, finalising),
handles graceful degradation across live, cached, mock, and rules_only modes,
and persists telemetry and boundary records.
Zero dependencies on app.adapters or app.api.
"""

import time
import uuid
from typing import Dict, Any, Optional, List
from app.ports.retrieval import RetrieverPort
from app.ports.llm import LLMPort
from app.ports.review_store import ReviewStorePort
from app.domain.review.models import ReviewContext, FindingItem
from app.domain.review.pipeline import (
    ExtractStage,
    RetrieveStage,
    AnalyseStage,
    ConfidenceFilterStage,
    GuardrailsStage,
    SuggestionValidatorStage,
)
from app.domain.review.verifier import LLMVerifierStage
from app.domain.review.sanitise import SanitiseStage
from app.domain.review.rule_engine import RuleChecksStage
from app.domain.review.accessibility import A11yChecksStage


class ReviewOrchestrator:
    """Application use case for executing and tracking review pipeline runs."""

    def __init__(
        self,
        store: ReviewStorePort,
        retriever: RetrieverPort,
        llm_adapter: LLMPort,
        default_mode: str = "mock",
        daily_cap: int = 100,
        model_name: str = "gemini-2.5-flash",
        verifier_enabled: bool = False,
        claim_confidence_threshold: float = 0.75,
    ):
        self.store = store
        self.retriever = retriever
        self.llm = llm_adapter
        self.default_mode = default_mode
        self.daily_cap = daily_cap
        self.model_name = model_name
        self.verifier_enabled = verifier_enabled
        self.claim_confidence_threshold = claim_confidence_threshold

    def run_review(
        self,
        review_id: str,
        submission_id: str,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None,
        user_max_tier: str = "internal",
    ) -> None:
        start_time = time.perf_counter()

        # 1. Fetch submission context
        sub = self.store.get_submission_context(submission_id)
        if not sub:
            self.store.fail_review(review_id, f"Submission '{submission_id}' not found")
            return

        # 2. Fetch KB pool
        kb_pool = self.store.get_kb_pool(user_max_tier=user_max_tier)

        # 3. Mode resolution and fallback checks
        no_external_ai = bool(self.store.get_setting("no_external_ai", False))
        cap_setting = self.store.get_setting("llm_daily_cap", self.daily_cap)
        daily_cap = int(cap_setting) if cap_setting is not None else self.daily_cap
        live_calls_today = self.store.get_daily_live_calls_count()

        effective_mode = self.default_mode.lower()
        fallback_reason = None

        if no_external_ai:
            if effective_mode == "live":
                effective_mode = "rules_only"
                fallback_reason = "Admin switch: external AI is disabled. Reverted to rules_only."
        elif effective_mode == "live":
            if daily_cap <= 0 or live_calls_today >= daily_cap:
                effective_mode = "rules_only"
                fallback_reason = f"Daily live LLM cap reached ({live_calls_today}/{daily_cap}). Falling back to rules_only."

        # 4. Initialize ReviewContext
        context = ReviewContext(
            text=sub.get("content", ""),
            channel=sub.get("channel", "social"),
            user_max_tier=user_max_tier,
            mode=effective_mode,
            kb_pool=kb_pool,
            metadata={"submission_id": submission_id},
        )

        try:
            # Step A: extracting (Extract + Sanitise)
            self.store.update_review_progress(review_id, "extracting")
            context = ExtractStage().process(context)
            context = SanitiseStage().process(context)

            # Step B: rule_checks (RuleChecks + A11yChecks)
            self.store.update_review_progress(review_id, "rule_checks")
            context = RuleChecksStage().process(context)
            context = A11yChecksStage().process(context)

            # Step C: retrieving (In-process BM25)
            self.store.update_review_progress(review_id, "retrieving")
            context = RetrieveStage(self.retriever).process(context)

            # Step D: analysing (LLM analysis with partial survival on error/timeout)
            self.store.update_review_progress(review_id, "analysing")
            if context.mode != "rules_only":
                try:
                    context = AnalyseStage(self.llm).process(context)
                except Exception as e:
                    fallback_reason = f"Model analysis error or timeout: {str(e)}. Rule findings preserved."

            # Filter low-confidence AI claim and tone findings before guardrails
            context = ConfidenceFilterStage(threshold=self.claim_confidence_threshold).process(context)

            # Step E: finalising (Guardrails + Verifier + Suggestions)
            self.store.update_review_progress(review_id, "finalising")
            context = GuardrailsStage().process(context)

            is_verifier_active = bool(self.store.get_setting("verifier_enabled", self.verifier_enabled))
            if is_verifier_active:
                context = LLMVerifierStage(llm_adapter=self.llm, enabled=True).process(context)

            # Generate suggestions if LLM is active
            if context.mode != "rules_only":
                try:
                    findings_needing_sugg = [f.to_dict() for f in context.findings if not f.suggested_fix]
                    if findings_needing_sugg:
                        sugg_list = self.llm.suggest_fixes(
                            sanitised_text=context.sanitised_text,
                            findings=findings_needing_sugg,
                            kb_entries=context.kb_retrieved,
                        )
                        sugg_map = {s["finding_id"]: s["suggested_fix"] for s in sugg_list if "finding_id" in s}
                        for f in context.findings:
                            if f.id in sugg_map:
                                f.suggested_fix = sugg_map[f.id]
                        context = SuggestionValidatorStage().process(context)
                except Exception as e:
                    # Suggestions fail gracefully without failing review
                    pass

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            stats = {
                "rules_evaluated": len(context.kb_pool),
                "kb_retrieved_count": len(context.kb_retrieved),
                "findings_count": len(context.findings),
                "latency_ms": elapsed_ms,
            }

            # Map KB codes to IDs
            code_to_entry = {e.get("code"): e for e in kb_pool if "code" in e}
            serialised_findings = []
            for item in context.findings:
                d = item.to_dict()
                if item.cited_entry_code and item.cited_entry_code in code_to_entry:
                    matched = code_to_entry[item.cited_entry_code]
                    d["cited_entry_id"] = matched.get("id")
                    d["cited_entry_version"] = matched.get("current_version", 1)
                serialised_findings.append(d)

            # Prepare AI call telemetry
            retrieved_codes = [e.get("code") for e in context.kb_retrieved if "code" in e]
            chars_sent = len(context.sanitised_text) if context.mode != "rules_only" else 0

            ai_call_data = {
                "purpose": "policy_and_claim_verification",
                "provider": "mock" if context.mode == "mock" else "Google AI Studio",
                "model": "mock-pipeline-v1" if context.mode == "mock" else self.model_name,
                "chars_sent": chars_sent,
                "redaction_summary": {
                    "redacted_items": len(context.redaction_log),
                },
                "kb_entry_ids": retrieved_codes,
                "max_tier_sent": "public" if context.mode == "mock" else "internal",
                "status": "success",
                "latency_ms": elapsed_ms,
                "tokens_in": chars_sent // 4 if chars_sent else 0,
                "tokens_out": len(context.findings) * 30,
                "cache_hit": (context.mode == "cached"),
            }

            # 5. Persist completed results
            self.store.save_review_results(
                review_id=review_id,
                submission_id=submission_id,
                submission_version_id=sub.get("current_version_id") or "v1",
                findings=serialised_findings,
                stats=stats,
                mode=context.mode,
                provider="Offline Mock Engine" if context.mode == "mock" else "Google AI Studio",
                model="mock-pipeline-v1" if context.mode == "mock" else self.model_name,
                ai_call_data=ai_call_data,
                fallback_reason=fallback_reason,
                actor_id=user_id,
                actor_role=user_role,
            )

        except Exception as err:
            self.store.fail_review(review_id, f"Review pipeline exception: {str(err)}")
