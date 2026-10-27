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

## 5. Empirical Evaluation Results: Verifier OFF vs. Verifier ON

The following empirical results were produced directly by running `python manage.py eval` against the complete 84-document benchmark in both `mock` and `cached` modes, before and after enabling the secondary `LLMVerifierStage`:

### Before-and-After Summary Table

| Execution Mode | Verifier Pass | Total Docs | Clean Pass Rate | TP | FP | FN | Precision | Recall | F1 Score | Target Adherence (P $\ge$ 0.85, R $\ge$ 0.80) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`mock`** | **OFF** | 84 | 81.0% | 66 | 7 | 19 | **0.904** | **0.776** | **0.835** | Precision Met (+0.054) / Recall Missed (-0.024) |
| **`mock`** | **ON** | 84 | 81.0% | 66 | 7 | 19 | **0.904** | **0.776** | **0.835** | Precision Met (+0.054) / Recall Missed (-0.024) |
| **`cached`** | **OFF** | 84 | 23.8% | 77 | 119 | 8 | **0.393** | **0.906** | **0.548** | Recall Exceeded (+0.106) / Precision Missed (-0.457) |
| **`cached`** | **ON** | 84 | 23.8% | 79 | 122 | 6 | **0.393** | **0.929** | **0.552** | Recall Exceeded (+0.129) / Precision Missed (-0.457) |

---

### Detailed Breakdown 1: Mode `mock` (Verifier: OFF)
```text
[Inkguard CLI] >> Running: .venv/bin/python -m app.eval.cli --mode mock --verifier off --out docs/evidence/eval_mock_off.json

### Evaluation Results: Mode `mock` (Verifier: OFF)
- Total Documents: 84 | Clean Documents: 21 (Clean Pass Rate: 81.0%)
- Overall: Precision: 0.904 | Recall: 0.776 | F1: 0.835 (TP: 66, FP: 7, FN: 19)

| Category | TP | FP | FN | Precision | Recall | F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `accessibility` | 0 | 1 | 1 | 0.000 | 0.000 | 0.000 |
| `claim` | 8 | 1 | 15 | 0.889 | 0.348 | 0.500 |
| `confidential_leak` | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| `general_note` | 0 | 1 | 0 | 0.000 | 1.000 | 0.000 |
| `missing_disclaimer` | 18 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| `readability` | 0 | 4 | 0 | 0.000 | 1.000 | 0.000 |
| `terminology` | 32 | 0 | 0 | 1.000 | 1.000 | 1.000 |
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

### Detailed Breakdown 2: Mode `mock` (Verifier: ON)
```text
[Inkguard CLI] >> Running: .venv/bin/python -m app.eval.cli --mode mock --verifier on --out docs/evidence/eval_mock_on.json

### Evaluation Results: Mode `mock` (Verifier: ON)
- Total Documents: 84 | Clean Documents: 21 (Clean Pass Rate: 81.0%)
- Overall: Precision: 0.904 | Recall: 0.776 | F1: 0.835 (TP: 66, FP: 7, FN: 19)

| Category | TP | FP | FN | Precision | Recall | F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `accessibility` | 0 | 1 | 1 | 0.000 | 0.000 | 0.000 |
| `claim` | 8 | 1 | 15 | 0.889 | 0.348 | 0.500 |
| `confidential_leak` | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| `general_note` | 0 | 1 | 0 | 0.000 | 1.000 | 0.000 |
| `missing_disclaimer` | 18 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| `readability` | 0 | 4 | 0 | 0.000 | 1.000 | 0.000 |
| `terminology` | 32 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| `tone` | 5 | 0 | 3 | 1.000 | 0.625 | 0.769 |
```

---

### Detailed Breakdown 3: Mode `cached` (Verifier: OFF)
```text
[Inkguard CLI] >> Running: .venv/bin/python -m app.eval.cli --mode cached --verifier off --out docs/evidence/eval_cached_off.json

### Evaluation Results: Mode `cached` (Verifier: OFF)
- Total Documents: 84 | Clean Documents: 21 (Clean Pass Rate: 23.8%)
- Overall: Precision: 0.393 | Recall: 0.906 | F1: 0.548 (TP: 77, FP: 119, FN: 8)

| Category | TP | FP | FN | Precision | Recall | F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `accessibility` | 0 | 1 | 1 | 0.000 | 0.000 | 0.000 |
| `claim` | 18 | 55 | 5 | 0.247 | 0.783 | 0.375 |
| `confidential_leak` | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| `general_note` | 0 | 42 | 0 | 0.000 | 1.000 | 0.000 |
| `missing_disclaimer` | 18 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| `readability` | 0 | 4 | 0 | 0.000 | 1.000 | 0.000 |
| `terminology` | 32 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| `tone` | 6 | 17 | 2 | 0.261 | 0.750 | 0.387 |

Claim Verdict Breakdown:
| Verdict | TP | FP | FN | Precision | Recall | F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `Contradicted` | 1 | 27 | 2 | 0.036 | 0.333 | 0.065 |
| `Expired` | 4 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| `Supported` | 7 | 18 | 1 | 0.280 | 0.875 | 0.424 |
| `Unverified` | 0 | 11 | 2 | 0.000 | 0.000 | 0.000 |
```

---

### Detailed Breakdown 4: Mode `cached` (Verifier: ON)
```text
[Inkguard CLI] >> Running: .venv/bin/python -m app.eval.cli --mode cached --verifier on --out docs/evidence/eval_cached_on.json

### Evaluation Results: Mode `cached` (Verifier: ON)
- Total Documents: 84 | Clean Documents: 21 (Clean Pass Rate: 23.8%)
- Overall: Precision: 0.393 | Recall: 0.929 | F1: 0.552 (TP: 79, FP: 122, FN: 6)

| Category | TP | FP | FN | Precision | Recall | F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `accessibility` | 0 | 1 | 1 | 0.000 | 0.000 | 0.000 |
| `claim` | 20 | 55 | 3 | 0.267 | 0.870 | 0.408 |
| `confidential_leak` | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| `general_note` | 0 | 46 | 0 | 0.000 | 1.000 | 0.000 |
| `missing_disclaimer` | 18 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| `readability` | 0 | 4 | 0 | 0.000 | 1.000 | 0.000 |
| `terminology` | 32 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| `tone` | 6 | 16 | 2 | 0.273 | 0.750 | 0.400 |

Claim Verdict Breakdown:
| Verdict | TP | FP | FN | Precision | Recall | F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `Contradicted` | 1 | 28 | 2 | 0.034 | 0.333 | 0.062 |
| `Expired` | 4 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| `Supported` | 8 | 17 | 0 | 0.320 | 1.000 | 0.485 |
| `Unverified` | 1 | 11 | 1 | 0.083 | 0.500 | 0.143 |
```

---

## 6. Honest Target Analysis & Error Breakdown

### Target Comparison (Target: Precision $\ge 0.85$, Recall $\ge 0.80$)

1. **Precision Target ($\ge 0.85$)**:
   - **`mock` Mode**: Achieved **0.904**, successfully exceeding the 0.85 target by **+0.054**.
   - **`cached` Mode**: Achieved **0.393**, **MISSING the target**.
2. **Recall Target ($\ge 0.80$)**:
   - **`mock` Mode**: Achieved **0.776**, narrowly missing the 0.80 target by **-0.024** due to ungrounded claims in offline fixtures.
   - **`cached` Mode**: Achieved **0.929**, successfully exceeding the 0.80 target by **+0.129** (79 out of 85 true ground-truth violations caught).

---

### Top False Positives

Analysis of the 122 False Positives in cached mode (`docs/evidence/eval_cached_on.json`) reveals three primary operational sources:

1. **Unsolicited Compliant Praise Notes (46 FPs)**:
   - The generative LLM (`gemini-3.5-flash-lite`) frequently emits advisory observations praising compliant copy (e.g., `doc-003`: *"Copy effectively reinforces natural skin diversity without making unverified or prohibited claims"*). Because the benchmark dataset only labels true negative/clean documents without policy infractions, emitting compliant praise notes is penalized as an ungrounded prediction.
2. **Compliant Claim Attributions (55 FPs)**:
   - The LLM emits findings with `claim_verdict="Supported"` acknowledging valid brand claims that do not violate policy (e.g., `doc-001`: *"The copy correctly specifies 'cold-pressed rosehip seed extract' instead of generic 'rosehip oil'"* citing `TERM-002`; `doc-002`: *"The copy correctly uses 'plant-derived ingredients' as preferred over misleading 'all-natural'"* citing `TERM-006`).
3. **Flesch-Kincaid Readability Warnings (4 FPs)**:
   - High reading-grade level warnings (grade 14–17) triggered on corporate/press release copy with complex chemical terms (`borosilicate glass`, `trans-epidermal water loss`).

---

### Top False Negatives

Across the benchmark, only 6 False Negatives occurred in cached mode:

1. **Accessibility Non-Descriptive Hyperlink (`RULE-A11Y-01`)**:
   - Missing detection of non-descriptive hyperlink anchor text in `doc-011`.
2. **Subtle Off-Tone Deviations (`TONE-002`, `TONE-004`)**:
   - In `doc-005` and `doc-009`, nuanced brand voice deviations were classified as borderline or compliant by the primary LLM analysis.
3. **Complex Clinical Claims (3 FNs)**:
   - Two contradicted efficacy claims and one unverified claim where the model failed to extract the candidate span during Stage 4 analysis.

---

### Real Bug Fixes vs. No Prompt-Fitting

In strict accordance with developer instructions, we did **not** adjust prompts or tune heuristics to artificially game or fit the evaluation benchmark. Only genuine code bugs were fixed:

- **`rule_engine.py` False Positive on Preferred Terminology**:
  - `TERM-014` data bans all-caps `"LUMO GLOW"` and prefers title-case `"Lumo Glow"`. Due to an uncased regex `re.compile(rf"\b{re.escape(banned)}\b", re.IGNORECASE)` without an equality exemption for `preferred`, the engine erroneously flagged text that was *already compliant* with the preferred term (`"Lumo Glow"`).
  - Adding `if preferred and excerpt == preferred: continue` in `rule_engine.py` eliminated 5 false positives, restoring terminology precision to **1.000** (32/32 TP, 0 FP).
