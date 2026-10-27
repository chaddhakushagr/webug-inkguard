# Lumo Skincare Brand Policy Evaluation Dataset

## Overview
This directory contains 84 hand-curated benchmark marketing copy documents for the fictional skincare brand **Lumo**. This dataset serves as the standardized test set for measuring Precision, Recall, and F1 on brand governance policy findings.

## Ground-Truth Labeling Methodology
In accordance with evaluation integrity standards, all 84 documents were **hand-labeled directly from the Lumo brand knowledge base (`backend/app/seed/lumo_brand.py`)** prior to running the review engine:
- **No Model Scraping**: Labels were written from authoritative guideline definitions, not by running the system and copying model predictions.
- **Character Offset Precision**: Every finding specifies exact 0-indexed character spans (`span_start` and `span_end`), strictly validated such that `text[span_start:span_end] == excerpt`.
- **Knowledge Base Grounding**: Every `entry_code` maps directly to an active seed knowledge base entry (`TERM-xxx`, `RULE-xxx`, `FACT-xxx`, `TONE-xxx`, `ASSET-xxx`).

## Dataset Composition (84 Documents Total)

### 1. Document Distribution by Channel
- **Social Media (`social`)**: 24 documents (short-form posts, hashtags, sponsorships).
- **Email Marketing (`email`)**: 18 documents (welcome series, product launches, newsletters).
- **Blog Articles (`blog`)**: 16 documents (educational deep-dives, ingredient spotlights).
- **Website Copy (`web`)**: 16 documents (product descriptions, ingredient glossaries, FAQs).
- **Press Releases (`press_release`)**: 10 documents (clinical milestones, sustainability announcements).

### 2. Clean vs. Violating Balance
- **Clean Documents**: 21 documents (**exactly 25.0%** of the dataset).
  - Clean documents contain zero policy violations, use approved terminology ("Lumo Glow Concentrate", "cold-pressed rosehip seed extract", "plant-derived ingredients"), and contain all required channel disclaimers (`#LumoPartner`, `Individual results may vary`, `Patch test advised`).
  - Essential for measuring false-positive rate and system specificity.
- **Violating & Adversarial Documents**: 63 documents (**75.0%** of the dataset).

### 3. Rule & Verdict Coverage Inventory
- **Terminology Rules (15 rules)**: Full coverage of `TERM-001` through `TERM-015`, testing banned cosmetic jargon ("serum", "cure", "miracle", "toxin-free", "chemical-free", "all-natural", "anti-aging", "pore-erasing", "flawless", "instant fix", "100% natural", "magic elixir", all-caps capitalization, and ungrounded "dermatologist approved").
- **Regulatory & Disclaimer Rules (10 rules)**:
  - `RULE-CLAIM-01`: Clinical efficacy triggers requiring proof citations ("clinically proven", "boosts collagen", "reduces wrinkles").
  - `RULE-CLAIM-02`: Market rank and superlatives ("#1", "unbeatable", "100% satisfaction").
  - `RULE-DISC-01`: Missing social sponsorship disclosures (`#LumoPartner`).
  - `RULE-DISC-02`: Missing web individual variance disclaimers (`Individual results may vary`).
  - `RULE-DISC-03`: Missing blog patch test advisories (`Patch test advised`).
  - `RULE-CONF-01`: Confidential launch leaks ("Project Lumina", "November 15", "Lumina Dew").
  - `RULE-HEALTH-01`: Prohibited prescription disease claims ("treats eczema", "cures psoriasis").
  - `RULE-A11Y-01`: Non-descriptive hyperlink guidance (`[click here]`).
  - `RULE-AMBIG-01`: Ambiguous superlatives ("revolutionary", "unrivaled").
- **All Four Claim Verdicts**:
  - `Supported`: Claims grounded by active clinical trials (e.g. FACT-001 94% hydration, FACT-006 DS-09 120 subjects, FACT-008 Patagonian sourcing, FACT-012 cruelty-free).
  - `Contradicted`: Claims refuted by clinical facts (e.g. medical cure refuted by FACT-001, synthetic origin refuted by FACT-008).
  - `Unverified`: Claims with no documented trial evidence (e.g. 2-day rapid radiance, guaranteed #1 formula).
  - `Expired`: Claims citing expired trials (e.g. FACT-002 Consumer Panel CP-08 expired June 2025, FACT-009 Formulation PF-01 expired Dec 2024).
- **Tricky Near-Misses & Safe Exceptions**:
  - Explicit rule exceptions: "hair serum" (exempted in `TERM-001`).
  - Substring word boundaries: "secure" and "curiosity" (contain substring "cure" but must not flag `TERM-004`).
  - Compliant disclaimers present: Ensuring presence of disclaimers does not trigger false missing-disclaimer flags.
- **Tone Deviations & Adversarial Injections**:
  - `TONE-003` boastful competitor disparagement.
  - `TONE-002` anxiety-inducing shame language.
  - `TONE-004` exclusionary perfectionism.
  - Prompt injection attacks attempting system override / instruction bypassing in copy.

## Schema
Each file `doc-XXX.json` adheres to:
```json
{
  "id": "doc-001",
  "channel": "social",
  "title": "Morning Glow Social Ritual",
  "text": "Start your morning ritual with Lumo Glow Concentrate. ...",
  "expected_findings": [
    {
      "entry_code": "TERM-001",
      "span_start": 45,
      "span_end": 50,
      "excerpt": "serum",
      "issue_type": "terminology",
      "verdict": null,
      "severity": "high"
    }
  ],
  "notes": "Description of why these labels were assigned"
}
```
