# Inkguard Policy Evaluation Harness & Benchmark Suite

This document specifies the architecture, methodology, ground-truth dataset, and empirical results of the **Inkguard Policy Evaluation Harness** (Round 3 Improvement 1). The harness provides a reproducible, honest benchmark measuring the **Precision, Recall, and F1** of policy findings against hand-curated marketing copy for the fictional skincare brand **Lumo**.

---

## 1. Objectives & Ground-Truth Philosophy

In accordance with [SUBMISSION_R2.md](file:///home/redpanda/Documents/WeBug/docs/SUBMISSION_R2.md#L125-L129) and [ROUND3_GAPS.md](file:///home/redpanda/Documents/WeBug/docs/ROUND3_GAPS.md#L12-L21), the evaluation system adheres to strict scoring principles:

1. **Independent Hand-Labeling**: All ground-truth annotations were authored **by hand directly from the seed knowledge base (`backend/app/seed/lumo_brand.py`)**, never by running the review engine and scraping its outputs.
2. **Exact Character Spans**: Every expected finding specifies exact character offsets `[span_start:span_end]`, validated by automated tests asserting `text[span_start:span_end] == excerpt`.
3. **Strict Negative Baseline**: Exactly **25.0% of the dataset consists of completely clean, compliant documents** to rigorously quantify False Positives and system specificity.
4. **Deterministic & Resumable Execution**: Deterministic modes (`rules_only`, `mock`, `cached`) produce identical metrics on every run. Live runs respect `LLM_DAILY_CAP` and cache responses to disk, enabling resumable batch evaluation across days without wasting quota.

---

## 2. Benchmark Dataset Specification

The evaluation dataset is located in `backend/app/eval/dataset/*.json`, consisting of **84 individual JSON documents** across all 5 marketing copy channels:

```text
backend/app/eval/dataset/
├── README.md               # Explanation of hand-labeling methodology
├── doc-001.json ... doc-084.json  # 84 hand-curated benchmark documents
```

### Document Distribution by Channel

| Channel | Document Count | Percentage | Typical Formats |
| :--- | :---: | :---: | :--- |
| **Social Media (`social`)** | 24 | 28.6% | Instagram captions, character limits, sponsorship hashtags (`#LumoPartner`) |
| **Email Marketing (`email`)** | 18 | 21.4% | Welcome journeys, product announcements, promotional newsletters |
| **Blog Articles (`blog`)** | 16 | 19.0% | Ingredient chemistry deep-dives, patch test advisories (`Patch test advised`) |
| **Website Copy (`web`)** | 16 | 19.0% | Product descriptions, clinical trial FAQ pages, variance disclaimers |
| **Press Releases (`press_release`)** | 10 | 11.9% | Corporate trial announcements, packaging sustainability certifications |
| **Total** | **84** | **100.0%** | |

### Balance & Category Breakdown

* **Clean Documents**: 21 documents (**25.0%**). These documents contain zero policy violations, adhere to all brand voice attributes, use approved terminology, and include all channel-required disclaimers.
* **Violating & Adversarial Documents**: 63 documents (**75.0%**).
  * **15 Terminology Rules (`TERM-001` to `TERM-015`)**: Full coverage of banned terms (e.g. "serum", "rosehip oil", "miracle", "cure", "anti-aging", "all-natural", "toxin-free", "chemical-free", "pore-erasing", "flawless", "instant fix", "dermatologist approved", "100% natural", "LUMO GLOW" capitalization, and "magic elixir").
  * **10 Regulatory & Governance Rules**:
    * `RULE-CLAIM-01`: Clinical efficacy triggers requiring proof citations ("clinically proven", "boosts collagen", "reduces wrinkles").
    * `RULE-CLAIM-02`: Market rank and superlatives ("#1", "unbeatable", "100% satisfaction").
    * `RULE-DISC-01`: Missing social sponsorship disclosures (`#LumoPartner`).
    * `RULE-DISC-02`: Missing web individual variance disclaimers (`Individual results may vary`).
    * `RULE-DISC-03`: Missing blog patch test advisories (`Patch test advised`).
    * `RULE-CONF-01`: Confidential launch leaks ("Project Lumina", "November 15", "Lumina Dew").
    * `RULE-HEALTH-01`: Prohibited prescription disease claims ("treats eczema", "cures psoriasis").
    * `RULE-A11Y-01`: Non-descriptive hyperlink guidance (`[click here]`).
    * `RULE-AMBIG-01`: Ambiguous superlatives ("revolutionary", "unrivaled").
  * **All 4 Claim Verdicts**:
    * `Supported`: Claims grounded by active clinical trials (FACT-001 94% hydration, FACT-006 DS-09 120 subjects, FACT-008 Patagonian sourcing, FACT-012 cruelty-free).
    * `Contradicted`: Claims refuted by clinical facts (e.g. medical cure refuted by FACT-001, synthetic origin refuted by FACT-008).
    * `Unverified`: Claims with no documented trial evidence (e.g. 2-day rapid radiance, guaranteed #1 formula).
    * `Expired`: Claims citing expired trials (FACT-002 Consumer Panel CP-08 expired June 2025, FACT-009 Formulation PF-01 expired Dec 2024).
  * **Tricky Near-Misses & Safe Exceptions**:
    * Explicit rule exceptions: "hair serum" (exempted in `TERM-001`).
    * Word boundaries: "secure" and "curiosity" (contain substring "cure" but must not flag `TERM-004`).
    * Disclaimer presence: Social, web, and blog posts with correct disclosures present.
  * **Tone & Adversarial Cases**:
    * Boastful competitor bashing (`TONE-003`).
    * Anxiety-inducing shame language (`TONE-002`).
    * Exclusionary perfectionism (`TONE-004`).
    * Prompt injection attacks attempting system override / instruction bypassing in copy.

---

## 3. Metrics & Matching Methodology

The evaluation harness uses **pure Python** ([metrics.py](file:///home/redpanda/Documents/WeBug/backend/app/eval/metrics.py)) with zero external math or ML dependencies.

### 1. Matching Criterion
A predicted finding $P$ matches a ground-truth expected finding $E$ if and only if:
1. **Entry Code Identity**: The cited knowledge base code matches exactly (case-insensitive):
   $$\text{code}(P) = \text{code}(E)$$
2. **Character Span Overlap**: The character spans overlap by at least 1 character:
   $$\max(\text{start}_P, \text{start}_E) < \min(\text{end}_P, \text{end}_E)$$
3. **Claim Verdict Match** (when verdict matching is evaluated):
   $$\text{verdict}(P) = \text{verdict}(E)$$

### 2. Greedy 1-to-1 Bipartite Matching
To prevent double-counting or inflating scores:
- Each expected finding can match at most **one** predicted finding (True Positive).
- If the model emits multiple duplicate predictions overlapping the same expected finding, only the first is counted as a **True Positive (TP)**; subsequent duplicates are penalized as **False Positives (FP)**.
- Unmatched predictions are **False Positives (FP)**.
- Unmatched expected findings are **False Negatives (FN)**.

### 3. Metric Formulas
$$\text{Precision} = \frac{TP}{TP + FP} \quad (\text{if } TP + FP = 0 \text{ and } FN = 0, \text{Precision} = 1.0)$$
$$\text{Recall} = \frac{TP}{TP + FN} \quad (\text{if } TP + FN = 0, \text{Recall} = 1.0)$$
$$F_1 = \frac{2 \times \text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$

---

## 4. CLI Usage Guide

The evaluation harness is integrated directly into the `manage.py` CLI:

```bash
# Run deterministic rules-only evaluation
python manage.py eval --mode rules_only --verifier off --out docs/evidence/eval_rules_only.json

# Run deterministic mock LLM evaluation
python manage.py eval --mode mock --verifier off --out docs/evidence/eval_mock.json

# Run cached LLM evaluation (replays saved disk responses)
python manage.py eval --mode cached --verifier off --out docs/evidence/eval_cached.json

# Run live LLM evaluation (respects LLM_DAILY_CAP and writes to cache)
python manage.py eval --mode live --verifier off --out docs/evidence/eval_live.json

# Run evaluation with secondary LLM verifier pass enabled
python manage.py eval --mode mock --verifier on --out docs/evidence/eval_mock_verifier.json
```

### CLI Options:
* `--mode`: Execution mode (`rules_only`, `mock`, `cached`, `live`). Default: `rules_only`.
* `--verifier`: Enable or disable secondary verifier pass (`on`, `off`). Default: `off`.
* `--out`: Path to write the full JSON evaluation report with error breakdown.
* `--limit`: Optional integer limiting the number of documents evaluated.

---

## 5. Baseline Evaluation Results

The following empirical results were produced directly by running `python manage.py eval` against the complete 84-document benchmark:

### Baseline 1: Mode `rules_only` (Verifier: OFF)
```text
[Inkguard CLI] >> Running: .venv/bin/python -m app.eval.cli --mode rules_only --verifier off --out docs/evidence/eval_rules_only.json

### Evaluation Results: Mode `rules_only` (Verifier: OFF)
- Total Documents: 84 | Clean Documents: 21 (Clean Pass Rate: 61.9%)
- Overall: Precision: 0.853 | Recall: 0.753 | F1: 0.800 (TP: 64, FP: 11, FN: 21)

| Category | TP | FP | FN | Precision | Recall | F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `accessibility` | 0 | 1 | 1 | 0.000 | 0.000 | 0.000 |
| `claim` | 6 | 1 | 17 | 0.857 | 0.261 | 0.400 |
| `confidential_leak` | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| `missing_disclaimer` | 18 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| `readability` | 0 | 4 | 0 | 0.000 | 1.000 | 0.000 |
| `terminology` | 32 | 5 | 0 | 0.865 | 1.000 | 0.928 |
| `tone` | 5 | 0 | 3 | 1.000 | 0.625 | 0.769 |

Claim Verdict Breakdown:
| Verdict | TP | FP | FN | Precision | Recall | F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `Contradicted` | 0 | 0 | 3 | 0.000 | 0.000 | 0.000 |
| `Expired` | 0 | 0 | 4 | 0.000 | 0.000 | 0.000 |
| `Supported` | 0 | 0 | 8 | 0.000 | 0.000 | 0.000 |
| `Unverified` | 0 | 0 | 2 | 0.000 | 0.000 | 0.000 |
```

### Baseline 2: Mode `mock` (Verifier: OFF)
```text
[Inkguard CLI] >> Running: .venv/bin/python -m app.eval.cli --mode mock --verifier off --out docs/evidence/eval_mock.json

### Evaluation Results: Mode `mock` (Verifier: OFF)
- Total Documents: 84 | Clean Documents: 21 (Clean Pass Rate: 61.9%)
- Overall: Precision: 0.846 | Recall: 0.776 | F1: 0.810 (TP: 66, FP: 12, FN: 19)

| Category | TP | FP | FN | Precision | Recall | F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `accessibility` | 0 | 1 | 1 | 0.000 | 0.000 | 0.000 |
| `claim` | 8 | 1 | 15 | 0.889 | 0.348 | 0.500 |
| `confidential_leak` | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| `general_note` | 0 | 1 | 0 | 0.000 | 1.000 | 0.000 |
| `missing_disclaimer` | 18 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| `readability` | 0 | 4 | 0 | 0.000 | 1.000 | 0.000 |
| `terminology` | 32 | 5 | 0 | 0.865 | 1.000 | 0.928 |
| `tone` | 5 | 0 | 3 | 1.000 | 0.625 | 0.769 |

Claim Verdict Breakdown:
| Verdict | TP | FP | FN | Precision | Recall | F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `Contradicted` | 1 | 0 | 2 | 1.000 | 0.333 | 0.500 |
| `Expired` | 0 | 0 | 4 | 0.000 | 0.000 | 0.000 |
| `Supported` | 0 | 0 | 8 | 0.000 | 0.000 | 0.000 |
| `Unverified` | 1 | 1 | 1 | 0.500 | 0.500 | 0.500 |
```

---

## 6. Error Analysis & Insights for Verifier Enhancement

Analysis of false positives and false negatives reveals clear operational boundaries between deterministic rule checks and semantic LLM checks:

1. **Deterministic Rule Checks Have High Precision**:
   - `missing_disclaimer`: **Precision: 1.000 | Recall: 1.000 | F1: 1.000** (18/18 True Positives, 0 False Positives).
   - `confidential_leak`: **Precision: 1.000 | Recall: 1.000 | F1: 1.000** (3/3 True Positives, 0 False Positives).
   - `terminology`: **Recall: 1.000 | Precision: 0.865** (32/32 True Positives).
2. **False Positives in Terminology / Readability**:
   - Generic readability warnings on longer copy segments (4 sentences $>30$ words) are emitted as advisory findings; these are categorized under non-policy general notes.
   - Compound terms (e.g. "100% natural" triggering both absolute percentage and natural term checks) can generate secondary findings on overlapping spans.
3. **False Negatives in Claims in Rules-Only Mode**:
   - In `rules_only` mode, clinical claims that do not contain explicit regex trigger words (`RULE-CLAIM-01`) cannot be semantically verified without the LLM analysis stage. Consequently, claim recall in rules-only mode is 0.261.
   - In `mock` mode, fixture matching identifies grounded claims (`Contradicted`, `Unverified`), elevating claim recall to 0.348 and F1 to 0.810.
4. **Target for LLM Verifier Pass (`G-01`)**:
   - Activating the secondary `LLMVerifierStage` with Google AI Studio live models will classify complex semantic claims (Supported, Contradicted, Expired, Unverified), bridging the remaining 15 claim false negatives and establishing CI regression gates of **Precision $\ge 0.85$ and Recall $\ge 0.80$**.
