"""
Unit tests for the secondary LLM Verifier stage (LLMVerifierStage).
Validates:
1. Finding with a real citation is kept (supported).
2. Citation that does not support the claim is dropped (not supported).
3. Unsure verdict becomes needs-human-judgment (not asserted).
4. AI down/timeout falls back to deterministic checks without error.
5. Confidential entry text is never sent to an external model (egress boundary).
"""

import pytest
from typing import Dict, Any
from app.domain.review.models import ReviewContext, FindingItem
from app.domain.review.verifier import LLMVerifierStage, deterministic_verify
from app.adapters.llm.openai_compatible import OpenAICompatibleLLMAdapter
from app.seed.lumo_brand import SEED_FACTS, SEED_TONE, SEED_TERMS


def test_verifier_supported_finding_kept():
    """1. Finding with a real, valid citation is verified as supported and kept."""
    stage = LLMVerifierStage(enabled=True)
    fact_001 = next(f for f in SEED_FACTS if f["code"] == "FACT-001")

    finding = FindingItem(
        id="find-001",
        source="ai",
        issue_type="claim",
        severity="high",
        confidence=0.92,
        span_start=10,
        span_end=35,
        excerpt="completely cure dry skin",
        explanation="Study L-12 supports hydration, refutes medical cure",
        cited_entry_code="FACT-001",
        claim_verdict="Contradicted",
        is_policy=True,
    )

    ctx = ReviewContext(
        text="This will completely cure dry skin in days.",
        kb_pool=[fact_001],
        findings=[finding],
    )

    result_ctx = stage.process(ctx)

    assert len(result_ctx.findings) == 1
    assert result_ctx.findings[0].id == "find-001"
    assert result_ctx.findings[0].verifier_verdict == "supported"
    assert "refutes" in result_ctx.findings[0].verifier_reason.lower() or "contradicts" in result_ctx.findings[0].verifier_reason.lower()


def test_verifier_unsupported_citation_dropped():
    """2. Citation that does not support the claim is dropped (filtered out)."""
    stage = LLMVerifierStage(enabled=True)
    fact_001 = next(f for f in SEED_FACTS if f["code"] == "FACT-001")

    # A finding citing FACT-001 (clinical skin hydration) for a totally unrelated cloud computing claim
    irrelevant_finding = FindingItem(
        id="find-002",
        source="ai",
        issue_type="claim",
        severity="high",
        confidence=0.90,
        span_start=0,
        span_end=38,
        excerpt="100% solar powered cloud infrastructure",
        explanation="Clinical study does not mention solar cloud servers",
        cited_entry_code="FACT-001",
        claim_verdict="Supported",
        is_policy=True,
    )

    ctx = ReviewContext(
        text="100% solar powered cloud infrastructure runs our operations.",
        kb_pool=[fact_001],
        findings=[irrelevant_finding],
    )

    result_ctx = stage.process(ctx)

    # Finding should be dropped because FACT-001 does not support solar cloud claim
    assert len(result_ctx.findings) == 0


def test_verifier_unsure_becomes_needs_human_judgment():
    """3. Unsure verdict becomes needs_human_judgment=True, not asserted or dropped."""
    stage = LLMVerifierStage(enabled=True)
    tone_001 = next(t for t in SEED_TONE if t["code"] == "TONE-001")

    # Finding with borderline confidence and ambiguous context
    ambiguous_finding = FindingItem(
        id="find-003",
        source="ai",
        issue_type="tone",
        severity="medium",
        confidence=0.55,  # Borderline confidence in unsure range
        span_start=0,
        span_end=20,
        excerpt="somewhat special serum",
        explanation="Borderline phrasing that requires context to judge",
        cited_entry_code="TONE-001",
        is_policy=True,
        needs_human_judgment=False,
    )

    ctx = ReviewContext(
        text="somewhat special serum for morning application.",
        kb_pool=[tone_001],
        findings=[ambiguous_finding],
    )

    result_ctx = stage.process(ctx)

    assert len(result_ctx.findings) == 1
    assert result_ctx.findings[0].verifier_verdict == "unsure"
    assert result_ctx.findings[0].needs_human_judgment is True


def test_verifier_ai_down_falls_back_without_error():
    """4. When external AI fails or times out, verifier falls back to deterministic checks gracefully."""
    class FailingLLMAdapter:
        def verify(self, finding, excerpt, cited_entry, prompt_version="v1"):
            raise RuntimeError("Google AI Studio upstream 503 Service Unavailable")

    stage = LLMVerifierStage(llm_adapter=FailingLLMAdapter(), enabled=True)
    fact_001 = next(f for f in SEED_FACTS if f["code"] == "FACT-001")

    finding = FindingItem(
        id="find-004",
        source="ai",
        issue_type="claim",
        severity="high",
        confidence=0.88,
        span_start=0,
        span_end=24,
        excerpt="cure dry skin completely",
        explanation="Medical cure claim refuted",
        cited_entry_code="FACT-001",
        claim_verdict="Contradicted",
        is_policy=True,
    )

    ctx = ReviewContext(
        text="cure dry skin completely in just 3 days.",
        mode="live",  # Mode live triggers adapter call
        kb_pool=[fact_001],
        findings=[finding],
    )

    # Must NOT raise exception; must fall back to deterministic verify
    result_ctx = stage.process(ctx)

    assert len(result_ctx.findings) == 1
    assert result_ctx.findings[0].verifier_verdict == "supported"
    assert "fallback" in result_ctx.findings[0].verifier_reason.lower()


def test_verifier_confidential_text_never_in_payload():
    """5. Confidential entry text is NEVER sent to an external model (egress boundary guard)."""
    fact_004_confidential = next(f for f in SEED_FACTS if f["code"] == "FACT-004")
    assert fact_004_confidential.get("classification") == "confidential"

    # 5a: Direct assertion on OpenAICompatibleLLMAdapter
    adapter = OpenAICompatibleLLMAdapter(api_key="test-key")
    finding_data = {
        "id": "find-conf",
        "issue_type": "claim",
        "explanation": "Confidential roadmap leak",
    }

    with pytest.raises(ValueError) as excinfo:
        adapter.verify(
            finding=finding_data,
            excerpt="Project Lumina launches November 15",
            cited_entry=fact_004_confidential,
        )
    assert "Security Invariant Violated: Confidential entry" in str(excinfo.value)

    # 5b: LLMVerifierStage intercepts confidential entries and diverts to offline check
    calls_made = []

    class SpyLLMAdapter:
        def verify(self, finding, excerpt, cited_entry, prompt_version="v1"):
            calls_made.append(cited_entry.get("code"))
            return {"verdict": "supported", "reason": "Spy verdict"}

    spy_adapter = SpyLLMAdapter()
    stage = LLMVerifierStage(llm_adapter=spy_adapter, enabled=True)

    conf_finding = FindingItem(
        id="find-conf-01",
        source="ai",
        issue_type="confidential_leak",
        severity="high",
        confidence=0.95,
        span_start=0,
        span_end=14,
        excerpt="Project Lumina",
        explanation="Secret project leak",
        cited_entry_code="FACT-004",
        is_policy=True,
    )

    ctx = ReviewContext(
        text="Project Lumina will revolutionize cosmetics.",
        mode="live",
        kb_pool=[fact_004_confidential],
        findings=[conf_finding],
    )

    result_ctx = stage.process(ctx)

    # Spy adapter must NEVER have been called with the confidential entry
    assert len(calls_made) == 0
    assert len(result_ctx.findings) == 1
    assert result_ctx.findings[0].verifier_verdict == "supported"
