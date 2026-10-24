# Round 3 Improvements Plan

This document details the three planned engineering initiatives for Round 3, including architectural designs, interfaces, and quantitative acceptance criteria.

---

## 1. Reliability Engine (Second-Pass Verifier & Calibration)

### Motivation
First-pass LLM extractions occasionally produce false-positive claim matches or slight hallucinated extrapolations. Round 3 introduces an automated two-pass verification loop with confidence calibration and a continuous evaluation harness.

### Technical Design
- **Verification Stage**: A targeted second-pass verifier LLM prompt:
  ```
  Given EXCERPT, CITED_FACT, and CLAIM_VERDICT:
  Verify whether CITED_FACT directly entails CLAIM_VERDICT for EXCERPT.
  Output: {verified: bool, calibration_score: float, contradiction_reason: str|null}
  ```
- **Evaluation Harness**: Benchmark suite of 100+ annotated synthetic marketing copy snippets with ground-truth policy citations.
- **Continuous Gate**: CI regression check ensuring model modifications maintain minimum metrics before deploy.

### Acceptance Criteria
- Policy finding precision $\ge 0.85$ across benchmark set.
- Policy finding recall $\ge 0.80$.
- Zero citations accepted without bidirectional entailment verification.

---

## 2. Guideline Health Intelligence (Ambiguity & Gap Detection)

### Motivation
Rules that are constantly dismissed or interpreted inconsistently across reviewers indicate unclear brand guidelines rather than author error.

### Technical Design
- **Ambiguity Scoring**:
  $$\text{Ambiguity}(R) = w_1 \cdot \text{DismissalRate}(R) + w_2 \cdot \text{ReviewerVariance}(R) + w_3 \cdot \text{OverrideEntropy}(R)$$
- **Gap Detection**: Unsupervised clustering of reviewer comment strings that cite no existing guideline code (`cited_entry_id IS NULL`), proposing candidate rules to brand managers.
- **Guideline Lifecycle**: Manager UI to retire, clarify, or re-word ambiguous rules with a historical impact projection view.

### Acceptance Criteria
- Flag rules with $>40\%$ dismissal rate across distinct reviewers.
- Cluster uncited reviewer comments into candidate rule drafts with sample occurrences.
- Impact simulation showing how rule wording adjustments alter historical finding rates.

---

## 3. Multi-Format Review (DOCX, PDF & Multimodal Brand Assets)

### Motivation
Marketing and PR assets rarely enter governance purely as raw text; they arrive as formatted PDF layouts, DOCX brochures, slide decks, and visual creative assets.

### Technical Design
- **Document Ingestion**: Headed document parser preserving structural metadata (headings, callout boxes, footnotes, tables).
- **Multimodal Visual Governance**:
  - Image OCR feeding into claim verification pipeline.
  - Mandatory alt-text verification for accessibility compliance.
  - Palette color-distance match ($\Delta E \le 2.0$ in CIELAB color space).
  - Logo placement and clearspace integrity verification via perceptual hashing.
- **Spatial Finding Mapping**: Bounding box coordinates returned with findings for interactive document viewer overlays.

### Acceptance Criteria
- Native extraction for PDF and DOCX documents with preserved reading order.
- Automated extraction and brand palette verification against registered asset colors.
- Interactive visual overlay displaying finding bounding boxes directly on rendered document pages.
