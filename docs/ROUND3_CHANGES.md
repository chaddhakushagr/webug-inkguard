# Round 3 Changes & Enhancements Report

**Product:** Inkguard — Intelligent Brand Governance Platform  
**Target:** Round 3 Final Submission Pack  
**Date:** October 2026

---

## Executive Summary

Between Round 2 and Round 3, Inkguard underwent major capability expansions and enterprise hardening:
1. **Three Core Architectural Improvements**: Reliability Engine & Verifier Pass, Guideline Health Intelligence & Gap Detection, and Multi-Format Review & Visual Brand Asset Compliance.
2. **All Round 2 Loose Ends Closed**: Channel normalization, review concurrency locks, empty content validation, admin reset demo API, and in-app notifications center.
3. **Robustness & Usability Polish**: 30-second execution deadlines with safe fallback, 60-second idempotency deduplication, daily cap HTTP headers, first-run guide, sample content picker, and 375px mobile responsiveness.
4. **Comprehensive Automated Test Coverage**: Total test suite expanded from 67 to **147 automated tests** (78 unit, 46 integration, 13 eval, 1 architecture, 9 end-to-end journeys), all passing with zero flakiness.

---

## 1. The Three Major Improvements

### Improvement 1: Reliability Engine & Evaluation Harness
- **What Was Built**:
  - **LLM Verifier Pass** ([verifier.py](file:///home/redpanda/Documents/WeBug/backend/app/domain/review/verifier.py)): Implemented `LLMVerifierStage` with a structured semantic entailment prompt ([verify.v1.md](file:///home/redpanda/Documents/WeBug/backend/app/prompts/verify.v1.md)). Every candidate finding emitted by the analysis stage is validated against the cited guideline text. If ungrounded or contradictory, it is dropped or downgraded to `needs_human_judgment=True`.
  - **Ground-Truth Evaluation Harness** ([eval/](file:///home/redpanda/Documents/WeBug/backend/app/eval/)): Built an automated benchmark runner (`python manage.py eval`) populated with **84 hand-curated marketing copy documents** across 5 channels (`Social`, `Email`, `Blog`, `Web`, `Press Release`).
  - **Empirical Precision/Recall Measurement**:
    - *Rules-Only Baseline*: Precision **0.915** | Recall **0.765** | F1 **0.833**
    - *Cached Mode without Verifier*: Precision **0.785** | Recall **0.871** | F1 **0.826**
    - *Cached Mode with Verifier*: Precision **0.884** | Recall **0.812** | F1 **0.846** (Eliminated 18 false positives)
- **Evidence Links**:
  - Tests: [test_verifier.py](file:///home/redpanda/Documents/WeBug/backend/tests/unit/test_verifier.py), [test_eval_runner.py](file:///home/redpanda/Documents/WeBug/backend/tests/eval/test_eval_runner.py)
  - Benchmark Reports: [eval_cached_on_v3.json](file:///home/redpanda/Documents/WeBug/docs/evidence/eval_cached_on_v3.json), [eval_rules_only.json](file:///home/redpanda/Documents/WeBug/docs/evidence/eval_rules_only.json)
  - Documentation: [docs/EVALUATION.md](file:///home/redpanda/Documents/WeBug/docs/EVALUATION.md)

### Improvement 2: Guideline Health Intelligence
- **What Was Built**:
  - **Mathematical Ambiguity Scoring Formula** ([ambiguity.py](file:///home/redpanda/Documents/WeBug/backend/app/domain/insights/ambiguity.py)): Evaluates active rules on a 0–100 scale incorporating creator dismissal rates, reviewer overrides, team discordance rates, and clarification comment volume (requires $\ge 5$ interaction events). Exposed via `GET /api/v1/insights/guideline-health`.
  - **Uncited Comment Clustering & Gap Detection** ([gaps.py](file:///home/redpanda/Documents/WeBug/backend/app/domain/insights/gaps.py)): In-process BM25 lexical clustering groups reviewer change-request comments that do not cite an existing rule. Generates candidate rule proposals into a brand manager review queue with one-click approval (`POST /api/v1/insights/gaps/{id}/approve`) into the Knowledge Base with version 1 and an immutable audit record.
  - **Rule Lifecycle Auditing** ([stale.py](file:///home/redpanda/Documents/WeBug/backend/app/domain/insights/stale.py)): Detects unused rules (8+ weeks), overdue review dates, expired facts, and rules referencing expired facts (`GET /api/v1/insights/stale`).
  - **Frontend Guideline Health Studio** (`/insights/guideline-health`): 3-tab interface featuring Ambiguous Rules with drill-down modals, Stale Rules with review links, and Gaps review/approval queue.
- **Evidence Links**:
  - Tests: [test_guideline_health.py](file:///home/redpanda/Documents/WeBug/backend/tests/unit/test_guideline_health.py), [test_guideline_health_router.py](file:///home/redpanda/Documents/WeBug/backend/tests/integration/test_guideline_health_router.py)
  - Screenshots: [gh-01-ambiguous-rules.png](file:///home/redpanda/Documents/WeBug/docs/evidence/gh-01-ambiguous-rules.png), [gh-04-gaps-proposals.png](file:///home/redpanda/Documents/WeBug/docs/evidence/gh-04-gaps-proposals.png), [gh-05-gap-approved-kb.png](file:///home/redpanda/Documents/WeBug/docs/evidence/gh-05-gap-approved-kb.png)
  - Documentation: [docs/GUIDELINE_HEALTH.md](file:///home/redpanda/Documents/WeBug/docs/GUIDELINE_HEALTH.md)

### Improvement 3: Multi-Format Review & Visual Brand Compliance
- **What Was Built**:
  - **Structural Document Parsing** ([docx_extractor.py](file:///home/redpanda/Documents/WeBug/backend/app/adapters/documents/docx_extractor.py), [pdf_extractor.py](file:///home/redpanda/Documents/WeBug/backend/app/adapters/documents/pdf_extractor.py)): Ingests `.docx` and `.pdf` files via `POST /api/v1/submissions/upload`, parses headings, tables, callouts, and extracts paragraph location metadata (`"Paragraph 3"`, `"Page 1"`).
  - **Computer-Vision Brand Compliance** ([image_extractor.py](file:///home/redpanda/Documents/WeBug/backend/app/adapters/documents/image_extractor.py), [color_math.py](file:///home/redpanda/Documents/WeBug/backend/app/domain/review/color_math.py)):
    - Pure Python CIE Lab Delta-E distance against brand palette (`PALETTE-001`).
    - 64-bit average perceptual image hashing verifying brand logo integrity (`ASSET-LOGO-01`).
    - WCAG AA 4.5:1 text/image contrast calculation.
    - Image intake safety: decompression bomb guards (`Image.MAX_IMAGE_PIXELS`), dimension caps (8192px), file size caps (10MB), and magic byte validation.
  - **Unified Upload UI**: Drag-and-drop file picker accepting `.docx`, `.pdf`, `.png`, `.jpg`, `.webp` that seamlessly collapses text input when a document is attached.
- **Evidence Links**:
  - Tests: [test_document_upload.py](file:///home/redpanda/Documents/WeBug/backend/tests/integration/test_document_upload.py), [test_image_checks.py](file:///home/redpanda/Documents/WeBug/backend/tests/unit/test_image_checks.py)
  - Fixtures: [good.docx](file:///home/redpanda/Documents/WeBug/backend/tests/fixtures/documents/good.docx), [text.pdf](file:///home/redpanda/Documents/WeBug/backend/tests/fixtures/documents/text.pdf), [lumo_logo.png](file:///home/redpanda/Documents/WeBug/backend/tests/fixtures/assets/lumo_logo.png)
  - Decision Document: [docs/decisions/OCR.md](file:///home/redpanda/Documents/WeBug/docs/decisions/OCR.md)

---

## 2. Declared Limitations & Technical Constraints

In accordance with Hackathon guidance, the following technical constraints were empirically investigated and handled:

### 1. Tesseract OCR in Headless Cloud Hosting
- **Constraint**: Running OCR on scanned images requires native C++ binary packages (`tesseract-ocr` and language data). In lightweight free-tier cloud environments (e.g. Render's 512 MB free tier), compiling or installing native OCR packages exceeds build memory limits and container image quotas.
- **Mitigation & Architectural Decision**:
  - Document extraction for `.docx` and digital `.pdf` runs 100% in pure Python with zero binary dependencies.
  - Visual brand asset checks (CIE Lab Delta-E color distance, perceptual logo hashing, contrast ratios) run 100% in pure Python without binary dependencies.
  - For image uploads where host OCR is absent (`shutil.which("tesseract") is None`), the pipeline gracefully degrades: it performs all visual asset checks, preserves the original uploaded binary, and informs the user (`"[Image submitted. OCR unavailable on this host; visual brand compliance checks applied]"`), completely eliminating 500 crashes while preserving security and usability.

### 2. Free-Tier LLM Rate Limits & Quotas
- **Constraint**: Google AI Studio's free tier enforces a strict 15 RPM / 1,500 RPD rate limit. Running two sequential LLM calls per document (analysis + verifier) across the 84-document evaluation harness consumes 168 requests, triggering rate limits on rapid execution.
- **Mitigation & Architectural Decision**:
  - Designed the offline evaluation cache in `backend/app/eval/cache/` keyed by `sha256(content|kb_codes|prompt_version|model)`, enabling instant, reproducible, zero-cost benchmark runs.
  - Implemented an enforced daily cap (`LLM_DAILY_CAP=100`) that automatically degrades to `rules_only` mode with the `X-LLM-Cap-Reached: true` HTTP header, preventing unexpected quota exhaustion.

---

## 3. Loose Ends Closed

The following technical gaps identified during Round 2 were completely resolved:

1. **G-14 (Channel Normalization)**:
   - Implemented `normalize_channel` and `get_risk_tier_for_channel` in `backend/app/domain/workflow/permissions.py`.
   - Variations such as `"Press Release"`, `"press-release"`, and `"PR"` properly map to `"press_release"` and `"high"` risk tier. Channel query filtering in `GET /submissions?channel=...` functions identically across all variations.
2. **G-15 (Idempotency & Concurrency Locks)**:
   - Added in-flight review status checks: triggering review on a submission whose review is already `pending` or `running` returns the existing review ID rather than spawning duplicate worker threads.
   - Disabled UI action buttons during in-flight mutations to eliminate double-click submission races.
3. **G-16 (Empty Content Validation)**:
   - Added min-length validation ($\ge 5$ characters) on `create_submission` and `update_submission_content`.
   - Added `file.size > 0` validation on `upload_document_submission`. Both return clean HTTP 422 before the review pipeline runs.
4. **F-67 (Reset-Demo Endpoints)**:
   - Mounted `GET /api/v1/admin/reset-demo` and `POST /api/v1/system/reset-demo` in FastAPI router with admin role gate and `ALLOW_SEED_RESET` guard.
5. **F-26 (In-App Push Notifications)**:
   - Created `Notification` database model, `GET /api/v1/notifications`, `POST /api/v1/notifications/{id}/read`.
   - Added top-bar notification bell with unread badge in `AppShell.tsx`.
   - Configured automatic notification triggers for creator and assignee on "Needs Second Approver" or "Approved".

---

## 4. Robustness (Phase 6) & Usability (Phase 7) Polish

1. **30-Second Timeout Wrapper**:
   - Added `execute_with_30s_timeout` with thread executor deadline enforcement in `openai_compatible.py`.
   - In `verifier.py`, caught timeouts and assigned an `"unsure"` verdict (`needs_human_judgment=True`) without 500 errors.
2. **60-Second Idempotency Deduplication**:
   - In `create_submission`, added support for `Idempotency-Key` / `X-Idempotency-Key` headers. Computes content hash and returns existing submission ID if submitted within 60 seconds by the same creator.
3. **Daily Cap HTTP Response Header**:
   - When daily live LLM calls reach `LLM_DAILY_CAP` (or cap is set to 0), review pipeline returns `X-LLM-Cap-Reached: true` across review creation and status polling.
4. **First-Run Guide Card**:
   - Renders a 3-step onboarding guide on the dashboard (*"Submit content → Review findings → Approve or fix"*) when a user has 0 submissions; includes permanent dismissal in `localStorage`.
5. **Sample Content Picker**:
   - Added a "Try a sample" selector on `/submissions/new` with 3 presets: Claim Violation (S1), Banned Term (S2), and Clean Copy (S3).
6. **Mobile Layout Polish at 375px**:
   - Polished `AppShell.tsx`, `submissions/new/page.tsx`, `submission/page.tsx`, and `FindingCard.tsx` to eliminate horizontal scroll (`overflow-x-hidden`), ensure tap targets are full-width, and truncate long headers.

---

## 5. Summary of Real Bugs Found & Resolved

| Bug Description | Root Cause | File & Line Fixed |
| :--- | :--- | :--- |
| **Silent Low Risk Tier for Press Releases** | String case mismatch in channel parameter | `backend/app/domain/workflow/permissions.py:48` |
| **Duplicate Findings on Rapid Double Click** | Unlocked review orchestration job launch | `backend/app/api/routers/submissions.py:1085` |
| **0-Byte Document & Empty Copy Reviews** | Missing min-length checks on input text | `backend/app/api/routers/submissions.py:248, 320` |
| **Missing Reset Demo Route in API** | Route not included in main router registration | `backend/app/api/routers/admin.py:18` |
| **Image Upload Deduplication Collision** | Content-hash deduplication applied to OCR fallback text | `backend/app/api/routers/submissions.py:260` |
| **Verifier Timeout 500 Error** | Unhandled upstream connection drop | `backend/app/domain/review/verifier.py:358` |
| **Header Casing in HTTP/2** | Test expected uppercase header; client received lowercase | `backend/tests/integration/test_phase6_robustness.py:84` |
| **375px Finding Action Button Clipping** | Fixed-width buttons overflowing flex row | `frontend/src/features/findings/FindingCard.tsx:334` |
| **E2E J3 Approval Assertion Mismatch** | Test asserted `approvals` array on `SubmissionDetail` | `backend/tests/e2e/test_main_journeys.py:344` |
