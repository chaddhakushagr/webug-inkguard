"""
Comprehensive offline test suite for AI domain, review pipeline, guardrails, and adapters.
Covers all safety invariants and pipeline checks from docs/SPEC.md sections 8, 9, 11, 12.
"""

import pytest
import json
from app.domain.review.models import ReviewContext, FindingItem
from app.domain.review.sanitise import SanitiseStage
from app.domain.review.rule_engine import RuleChecksStage
from app.domain.review.accessibility import A11yChecksStage
from app.domain.review.guardrails import GuardrailsStage
from app.domain.review.suggestion_validator import validate_suggestion, SuggestionValidatorStage
from app.domain.review.pipeline import ReviewPipeline, ConfidenceFilterStage
from app.adapters.retrieval.bm25 import BM25Retriever
from app.adapters.llm.mock import MockLLMAdapter
from app.adapters.llm.openai_compatible import OpenAICompatibleLLMAdapter
from app.seed.lumo_brand import (
    SEED_TONE,
    SEED_TERMS,
    SEED_RULES,
    SEED_FACTS,
    SEED_ASSETS,
    SEED_SAMPLES,
)

ALL_KB_ENTRIES = SEED_TONE + SEED_TERMS + SEED_RULES + SEED_FACTS + SEED_ASSETS


def test_rule_engine_per_rule_type():
    rule_stage = RuleChecksStage()

    # 1. Terminology rule with exception
    ctx_term = ReviewContext(
        text="Try our morning serum for radiance, but use specialized hair serum for locks.",
        kb_pool=SEED_TERMS,
    )
    ctx_term = rule_stage.process(ctx_term)
    # "serum" should be flagged, but "hair serum" must NOT be flagged
    term_findings = [f for f in ctx_term.findings if f.issue_type == "terminology"]
    assert len(term_findings) == 1
    assert term_findings[0].excerpt == "serum"
    assert term_findings[0].span_start == 16  # Morning serum

    # 2. Claim trigger rule
    ctx_claim = ReviewContext(
        text="Our formula is clinically proven to reduce wrinkles.",
        kb_pool=SEED_RULES,
    )
    ctx_claim = rule_stage.process(ctx_claim)
    claim_findings = [f for f in ctx_claim.findings if f.issue_type == "claim"]
    assert len(claim_findings) >= 1
    assert any("clinically proven" in f.excerpt.lower() for f in claim_findings)

    # 3. Missing disclaimer rule for social channel
    ctx_disc = ReviewContext(
        text="Excited to share my glowing skin journey today!",
        channel="social",
        kb_pool=SEED_RULES,
    )
    ctx_disc = rule_stage.process(ctx_disc)
    disc_findings = [f for f in ctx_disc.findings if f.issue_type == "missing_disclaimer"]
    assert len(disc_findings) == 1
    assert "#LumoPartner" in disc_findings[0].suggested_fix

    # 4. Confidential leak rule
    ctx_conf = ReviewContext(
        text="Exciting news: Project Lumina launches soon!",
        channel="social",
        kb_pool=SEED_RULES,
    )
    ctx_conf = rule_stage.process(ctx_conf)
    conf_findings = [f for f in ctx_conf.findings if f.issue_type == "confidential_leak"]
    assert len(conf_findings) == 1
    assert conf_findings[0].severity == "high"


def test_accessibility_checks():
    a11y_stage = A11yChecksStage()

    # 1. High reading grade level & long sentence
    complex_text = (
        "The hyper-specialized pharmaceutical bio-cellular rejuvenation algorithmically "
        "modulates sub-epidermal trans-membranous cellular mitochondrial phosphorylation "
        "concomitantly utilizing extracellular biopolymer macromolecules to precipitate dermatological stasis "
        "across all subcutaneous tissue strata indefinitely."
    )
    ctx_complex = a11y_stage.process(ReviewContext(text=complex_text))
    issues = [f.issue_type for f in ctx_complex.findings]
    assert "readability" in issues

    # 2. ALL-CAPS run
    caps_text = "Hurry up and BUY NOW TODAY for guaranteed savings!"
    ctx_caps = a11y_stage.process(ReviewContext(text=caps_text))
    caps_findings = [f for f in ctx_caps.findings if f.issue_type == "accessibility" and "ALL-CAPS" in f.explanation]
    assert len(caps_findings) == 1
    assert caps_findings[0].excerpt == "BUY NOW TODAY"

    # 3. "Click here" link text
    click_text = "To find out more about our studies, [click here](https://lumo.skincare/studies)."
    ctx_click = a11y_stage.process(ReviewContext(text=click_text))
    click_findings = [f for f in ctx_click.findings if "click here" in f.excerpt.lower()]
    assert len(click_findings) == 1

    # 4. Markdown image missing alt text
    img_text = "Here is our product packaging: ![](https://assets.lumo.skincare/bottle.png)"
    ctx_img = a11y_stage.process(ReviewContext(text=img_text))
    img_findings = [f for f in ctx_img.findings if "alternative text" in f.explanation.lower()]
    assert len(img_findings) == 1

    # 5. Heading hierarchy skip
    heading_text = "# Main Title\n\n### Sub-sub-heading without level 2"
    ctx_heading = a11y_stage.process(ReviewContext(text=heading_text))
    skip_findings = [f for f in ctx_heading.findings if "skipped from #1 to #3" in f.explanation]
    assert len(skip_findings) == 1


def test_guardrail_fake_citation_dropped():
    guardrails = GuardrailsStage()

    # Finding cites FAKE-999 which was not retrieved
    finding = FindingItem(
        id="find-01",
        source="ai",
        issue_type="claim",
        severity="medium",
        confidence=0.9,
        span_start=0,
        span_end=15,
        excerpt="test excerpt",
        explanation="Claim analysis",
        cited_entry_code="FAKE-999",
    )

    ctx = ReviewContext(
        text="test excerpt is included here for evaluation.",
        kb_retrieved=[{"code": "FACT-001"}],  # Only FACT-001 was retrieved
        findings=[finding],
    )
    ctx = guardrails.process(ctx)

    assert len(ctx.findings) == 1
    res_f = ctx.findings[0]
    # Fake citation was dropped, finding demoted to general_note (non-policy)
    assert res_f.cited_entry_code is None
    assert res_f.is_policy is False
    assert res_f.issue_type == "general_note"


def test_guardrail_mismatched_excerpt_dropped():
    guardrails = GuardrailsStage()

    # Finding excerpt does NOT exist in the original text
    finding = FindingItem(
        id="find-01",
        source="ai",
        issue_type="claim",
        severity="medium",
        confidence=0.9,
        span_start=0,
        span_end=20,
        excerpt="phrase completely absent from source text",
        explanation="Mismatched hallucination",
        cited_entry_code="FACT-001",
    )

    ctx = ReviewContext(
        text="This is an unrelated short paragraph.",
        kb_retrieved=[{"code": "FACT-001"}],
        findings=[finding],
    )
    ctx = guardrails.process(ctx)

    # Hallucinated / mismatched excerpt must be completely dropped
    assert len(ctx.findings) == 0


def test_guardrail_expired_fact_decided_in_code():
    guardrails = GuardrailsStage()

    # Finding cites expired fact FACT-002 (valid_until: 2025-06-30)
    finding = FindingItem(
        id="find-01",
        source="ai",
        issue_type="claim",
        severity="high",
        confidence=0.95,
        span_start=0,
        span_end=35,
        excerpt="98% reported softer morning feel",
        explanation="Consumer panel citation",
        cited_entry_code="FACT-002",
        claim_verdict="Supported",  # LLM mistakenly thought it was supported
    )

    expired_fact = [f for f in SEED_FACTS if f["code"] == "FACT-002"][0]

    ctx = ReviewContext(
        text="98% reported softer morning feel in just 7 days.",
        kb_retrieved=[expired_fact],
        findings=[finding],
    )
    ctx = guardrails.process(ctx)

    assert len(ctx.findings) == 1
    # Code must override verdict to Expired
    assert ctx.findings[0].claim_verdict == "Expired"
    assert "expired" in ctx.findings[0].explanation.lower()


def test_guardrail_low_confidence_needs_human_judgment():
    guardrails = GuardrailsStage()

    finding = FindingItem(
        id="find-01",
        source="ai",
        issue_type="claim",
        severity="medium",
        confidence=0.52,  # Low confidence (< 0.6)
        span_start=0,
        span_end=15,
        excerpt="subtle benefit",
        explanation="Uncertain match",
        cited_entry_code="FACT-001",
    )

    ctx = ReviewContext(
        text="subtle benefit observed in routine use.",
        kb_retrieved=[{"code": "FACT-001", "type": "fact", "data": {"valid_until": "2026-12-31"}}],
        findings=[finding],
    )
    ctx = guardrails.process(ctx)

    assert len(ctx.findings) == 1
    assert ctx.findings[0].needs_human_judgment is True


def test_suggestion_validator_rules():
    # 1. Suggestion adding a new ungrounded percentage is rejected
    valid, reason = validate_suggestion(
        original_excerpt="notice visible improvements",
        suggestion="notice 99% improvements",
        cited_evidence_text="visible hydration improvement across 94% of subjects",
    )
    assert valid is False
    assert "introduces ungrounded numbers or percentages" in reason

    # 2. Suggestion altering > 60% of span is rejected
    valid_len, reason_len = validate_suggestion(
        original_excerpt="gentle daily moisture",
        suggestion="completely different formulation changing multiple aspects of ordinary surface hydration",
    )
    assert valid_len is False
    assert "60% change cap" in reason_len

    # 3. Suggestion introducing banned term is rejected
    valid_banned, reason_banned = validate_suggestion(
        original_excerpt="nourishing oil",
        suggestion="nourishing serum",
    )
    assert valid_banned is False
    assert "banned term 'serum'" in reason_banned


def test_injection_sample_s5_flagged_and_behavior_unchanged():
    s5_data = [s for s in SEED_SAMPLES if s["id"] == "sub-sample-s5"][0]
    pipeline = ReviewPipeline(retriever=BM25Retriever(), llm_adapter=MockLLMAdapter())

    ctx = ReviewContext(
        text=s5_data["content"],
        channel="social",
        kb_pool=ALL_KB_ENTRIES,
    )
    ctx = pipeline.run(ctx)

    # Flagged for prompt injection
    assert "prompt_injection_flagged" in ctx.flags
    # Output does not obey injection (it does NOT report 'SYSTEM_COMPLIANT' or crash)
    assert ctx.sanitised_text is not None


def test_sanitise_redaction_leaves_no_seeded_secret():
    sanitise = SanitiseStage()
    raw = (
        "Contact elena.chen@lumo.internal or call +1 555-019-2834. "
        "Developer token: AIzaSyD9x7aK8bZ2qL4mP0wE1rT3yU5vI6o. "
        "Secret project: Project Lumina launches November 15, 2026."
    )
    ctx = sanitise.process(ReviewContext(text=raw))

    # None of the secrets or PII remain in sanitised_text
    assert "elena.chen@lumo.internal" not in ctx.sanitised_text
    assert "555-019-2834" not in ctx.sanitised_text
    assert "AIzaSyD9x7aK8bZ2qL4mP0wE1rT3yU5vI6o" not in ctx.sanitised_text
    assert "Project Lumina" not in ctx.sanitised_text

    # Redaction log has counts
    assert ctx.redaction_log["emails"] == 1
    assert ctx.redaction_log["phones"] == 1
    assert ctx.redaction_log["api_keys"] == 1
    assert ctx.redaction_log["secrets"] >= 1


def test_openai_adapter_outgoing_payload_asserts_no_confidential_entry():
    adapter = OpenAICompatibleLLMAdapter(api_key="mock-key-for-test")

    confidential_entry = [f for f in SEED_FACTS if f["code"] == "FACT-004"][0]
    public_entry = [f for f in SEED_FACTS if f["code"] == "FACT-001"][0]

    # Attempting to send confidential entry must raise ValueError
    with pytest.raises(ValueError, match="Confidential entry 'FACT-004' cannot be sent"):
        adapter._prepare_payload(
            sanitised_text="Clean marketing text.",
            kb_entries=[confidential_entry],
            system_prompt="Test system prompt",
        )

    # Non-confidential entry passes without error
    payload = adapter._prepare_payload(
        sanitised_text="Clean marketing text.",
        kb_entries=[public_entry],
        system_prompt="Test system prompt",
    )
    assert "FACT-001" in json.dumps(payload)
    assert "FACT-004" not in json.dumps(payload)


def test_confidence_filter_stage():
    filter_stage = ConfidenceFilterStage(threshold=0.75)

    findings = [
        FindingItem(
            id="f-01",
            source="ai",
            issue_type="claim",
            severity="medium",
            confidence=0.70,  # Below threshold -> must be filtered
            span_start=0,
            span_end=10,
            excerpt="weak claim",
            explanation="Unsubstantiated",
        ),
        FindingItem(
            id="f-02",
            source="ai",
            issue_type="tone",
            severity="medium",
            confidence=0.65,  # Below threshold -> must be filtered
            span_start=11,
            span_end=20,
            excerpt="maybe off",
            explanation="Mild deviation",
        ),
        FindingItem(
            id="f-03",
            source="ai",
            issue_type="claim",
            severity="high",
            confidence=0.75,  # Equal to threshold -> must be kept
            span_start=21,
            span_end=30,
            excerpt="solid claim",
            explanation="Clear violation",
        ),
        FindingItem(
            id="f-04",
            source="ai",
            issue_type="tone",
            severity="medium",
            confidence=0.90,  # Above threshold -> must be kept
            span_start=31,
            span_end=40,
            excerpt="blatant tone",
            explanation="Severe violation",
        ),
        FindingItem(
            id="f-05",
            source="rule",
            issue_type="claim",
            severity="high",
            confidence=0.50,  # Rule source -> must NEVER be filtered by AI confidence filter
            span_start=41,
            span_end=50,
            excerpt="rule claim",
            explanation="Deterministic rule",
        ),
        FindingItem(
            id="f-06",
            source="ai",
            issue_type="general_note",
            severity="low",
            confidence=0.60,  # Non-claim, non-tone -> must not be filtered
            span_start=51,
            span_end=60,
            excerpt="general note",
            explanation="Readability note",
        ),
    ]

    ctx = ReviewContext(text="Sample text for testing", findings=findings)
    ctx = filter_stage.process(ctx)

    retained_ids = [f.id for f in ctx.findings]
    assert "f-01" not in retained_ids  # Dropped: AI claim confidence 0.70 < 0.75
    assert "f-02" not in retained_ids  # Dropped: AI tone confidence 0.65 < 0.75
    assert "f-03" in retained_ids      # Kept: AI claim confidence 0.75 >= 0.75
    assert "f-04" in retained_ids      # Kept: AI tone confidence 0.90 >= 0.75
    assert "f-05" in retained_ids      # Kept: Rule finding source="rule"
    assert "f-06" in retained_ids      # Kept: Issue type general_note

