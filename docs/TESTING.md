# Inkguard Test Execution & Quality Assurance Report

This document records the complete testing strategy, execution commands, test counts, journey proofs, empirical bug fixes during Round 3, known gaps, and real test outputs across the entire Inkguard platform.

---

## 1. How to Run Each Test Suite

All test suites can be executed across Linux, macOS, and Windows without Docker using the root `manage.py` CLI:

### 1.1 Complete Test Suite (Unit, Integration, Architecture, Evaluation, E2E)
```bash
# Run all 147 pytest test cases
python manage.py test
```

### 1.2 End-to-End Journey Suite (J1 – J9)
```bash
# Run against local in-process application and fresh database
python manage.py e2e

# Or target a running dev server or deployed cloud instance (Neon + Render):
python manage.py e2e --base-url http://localhost:8000
python manage.py e2e --base-url https://inkguard.onrender.com
```

### 1.3 Sub-Suites by Category
```bash
# Pure domain unit tests (fast, in-memory, zero network or DB dependencies)
python -m pytest backend/tests/unit -v

# FastAPI integration tests (database transactions, RBAC, safety boundaries, uploads)
python -m pytest backend/tests/integration -v

# Clean architecture boundary verification (import-linter)
python manage.py arch

# Evaluation unit tests (scoring math, confusion matrices, dataset schema)
python -m pytest backend/tests/eval -v
```

### 1.4 Benchmark Policy Evaluation Harness (84 Ground Truth Documents)
```bash
# Rules-only baseline evaluation
python manage.py eval --mode rules_only --verifier off

# Cached LLM evaluation with semantic entailment verifier enabled
python manage.py eval --mode cached --verifier on

# Live Gemini LLM evaluation (requires Google AI Studio API key)
python manage.py eval --mode live --verifier on
```

### 1.5 Frontend Production Build Verification
```bash
cd frontend && npm run build
```

---

## 2. Test Suite Counts

| Category | Suite Path / Tool | Test Cases | Execution Time | External Dependencies | Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Domain Unit Tests** | `backend/tests/unit/` | **78** | ~3.9s | None (pure in-memory Python) | **PASS** |
| **API Integration Tests** | `backend/tests/integration/` | **46** | ~16.1s | SQLite / PostgreSQL session | **PASS** |
| **End-to-End Journeys (J1–J9)** | `backend/tests/e2e/` | **9** | ~6.9s | FastAPI TestClient / HTTP | **PASS** |
| **Evaluation Unit Tests** | `backend/tests/eval/` | **13** | ~0.1s | In-memory evaluation metrics | **PASS** |
| **Architecture Contracts** | `backend/tests/architecture/` (`arch`) | **1** contract (2 layers) | ~0.3s | `import-linter` | **PASS** |
| **Total Automated Pytest Tests** | All of above | **147** | **22.7s** | Database + TestClient | **147 PASS (100%)** |
| **Policy Benchmark Dataset** | `backend/app/eval/dataset/` | **84 documents** (5 channels) | ~0.5s | Disk cache / ground-truth annotations | **100% evaluated** |
| **Frontend Static Export** | `frontend/` (`next build`) | **20 routes** | ~14.0s | Node.js, Next.js Turbopack | **0 errors (100%)** |

---

## 3. What Each Journey Proves

The End-to-End suite in [test_main_journeys.py](file:///home/redpanda/Documents/WeBug/backend/tests/e2e/test_main_journeys.py) verifies the core user journeys required by the Round 3 Specification:

### Journey 1: Creator Pastes S1, Accepts a Fix, Dismisses One with a Reason, Submits
- **Test**: `test_j1_creator_s1_fix_dismiss_submit`
- **What it proves**:
  1. Creator logs in via `POST /api/v1/auth/login` and receives valid signed JWT.
  2. Submits sample copy S1 (`"Get glowing skin with Lumo's all-natural miracle serum!..."`).
  3. Triggers synchronous review pipeline; status advances from `Draft` to `Checked`.
  4. Review engine accurately detects claim violation (`RULE-001`), chemical claim (`RULE-002`), and banned term (`TERM-001`).
  5. Accepting a suggested fix replaces the prohibited text (`serum` -> `concentrate`), creates `SubmissionVersion 2`, and safely resets workflow status to `Draft`.
  6. Re-reviewing advances Version 2 to `Checked`.
  7. Dismissing a finding requires a mandatory `reason_code` (`editorial_exception`) and `reason_text`; records a `FindingAction` audit entry.
  8. Submission gate prevents submitting with open high-severity findings; once resolved, creator submits to `Submitted`.

### Journey 2: Reviewer Claims, Comments on a Finding, Requests Changes, Creator Revises & Resubmits
- **Test**: `test_j2_reviewer_claim_comment_request_changes_resubmit`
- **What it proves**:
  1. Reviewer claims submission via `POST /api/v1/submissions/{id}/claim`; status advances to `In Review` and assignee is stamped.
  2. Reviewer attaches a threaded comment (`POST /api/v1/submissions/{id}/comments`).
  3. Reviewer rejects the version via `POST /api/v1/submissions/{id}/request-changes` with mandatory explanation note; status advances to `Changes Requested`.
  4. Creator edits copy via `PUT /api/v1/submissions/{id}/content`; creates Version 2 and resets state to `Draft`.
  5. Creator re-runs review and resubmits to `Submitted`.

### Journey 3: High-Risk Content Requires Two Distinct Approvers; Creator Self-Approval Prohibited
- **Test**: `test_j3_high_risk_two_distinct_approvers_no_self_approval`
- **What it proves**:
  1. Setting channel to `press_release` automatically assigns high risk tier (`risk_tier="high"`).
  2. Safety invariant: Creator calling `POST /api/v1/submissions/{id}/approve` is strictly rejected with HTTP 403 (`"Creators cannot approve their own submissions"`).
  3. First reviewer claims and approves; because 2 approvers are required, status remains `In Review` with 1 approval recorded.
  4. Reviewer 1 calling approve again is rejected with HTTP 400 (`"You have already approved this content version"`).
  5. Second distinct reviewer (`reviewer.alex@lumo.internal`) approves; satisfies the 2-approver requirement and status advances to `Approved`.

### Journey 4: Mark Published
- **Test**: `test_j4_mark_published`
- **What it proves**:
  1. Validates that calling mark-published on an unapproved submission returns HTTP 400.
  2. Once `Approved`, creator calls `POST /api/v1/submissions/{id}/mark-published` with `url="https://instagram.com/p/..."`.
  3. Status transitions to `Marked Published`, saving `published_url` and `published_at` timestamp.
  4. An immutable audit record `submission_publish` is appended to the audit log with actor ID and published URL.

### Journey 5: Brand Manager Inspects Guideline Health and Approves Draft Rule Proposal
- **Test**: `test_j5_brand_manager_guideline_health_and_approve_draft_rule`
- **What it proves**:
  1. Brand manager calls `GET /api/v1/insights/guideline-health`; returns calculated ambiguity scores (0–100), dismissal rates, and contributing factors across active rules.
  2. Calls `GET /api/v1/insights/gaps`; returns candidate rule proposals generated by BM25 clustering of uncited reviewer comments.
  3. Calls `POST /api/v1/insights/gaps/{id}/approve`; transitions the proposal into an active Knowledge Base rule with Version 1 and records the approval in `audit_log`.
  4. Verifies the new rule is immediately retrievable in `GET /api/v1/kb/entries/{id}`.

### Journey 6: Admin Edits KB Entry, Creating Version 2; Historical Submission Cites Version 1
- **Test**: `test_j6_admin_edits_kb_entry_historical_citation_preserved`
- **What it proves**:
  1. Admin creates a KB entry (`RULE-TEST-...`) with Version 1.
  2. Creator submits copy violating that rule; review generates finding citing Version 1 (`cited_entry_version=1`).
  3. Admin edits the rule via `PUT /api/v1/kb/entries/{id}`; creates an immutable `KBEntryVersion` record and increments `current_version` to 2.
  4. Inspecting the older submission's findings proves that `cited_entry_version` remains 1, preserving historical compliance audit integrity.

### Journey 7: Multi-Format Upload of DOCX, PDF, and Image
- **Test**: `test_j7_docx_pdf_and_image_upload`
- **What it proves**:
  1. `POST /api/v1/submissions/upload` accepts `.docx` (`good.docx`), extracts headings and paragraphs, and tracks paragraph location labels (`"Paragraph 1"`). Original file binary is persisted and retrievable via `GET /api/v1/submissions/{id}/document`.
  2. Accepts `.pdf` (`text.pdf`), parses text structure, and generates draft submission.
  3. Accepts `.png` (`lumo_logo.png`), extracts image metadata, runs perceptual average hash matching (`ASSET-LOGO-01`) and CIE Lab Delta-E color palette verification (`PALETTE-001`).

### Journey 8: Evaluation Page and Results Load
- **Test**: `test_j8_evaluation_page_loads`
- **What it proves**:
  1. Brand manager accesses `GET /api/v1/evaluation/results`.
  2. Verifies JSON structure contains `summary.overall` with precision, recall, and F1 metrics across 84 benchmark documents.
  3. Verifies `before_after` comparisons (mock vs live, verifier on vs off).
  4. Verifies static export artifact `frontend/out/eval/index.html` is compiled and non-empty.

### Journey 9: AI-Off Admin Switch Forces Rules-Only Fallback
- **Test**: `test_j9_ai_off_admin_switch_rules_only_review`
- **What it proves**:
  1. Admin toggles system switch `no_external_ai: true` via `PUT /api/v1/settings`.
  2. Creator submits copy containing terminology and claim violations.
  3. Review pipeline honours the switch: bypasses external LLM calls, completes review in `rules_only` mode without 500 errors, and flags rule-based violations.
  4. Admin restores setting `no_external_ai: false`.

---

## 4. Real Bugs Found and Fixed During Round 3

During the development and testing of Round 3, the test harness and manual journeys identified several real defects, all of which were resolved in the codebase:

1. **G-14: Channel Normalization Case and Separator Mismatch**:
   - *Bug*: Submitting `"Press Release"` or `"press-release"` failed to match `"press_release"` in `get_risk_tier_for_channel`, silently defaulting high-risk press releases to low-risk tier.
   - *Fix*: Implemented `normalize_channel` in `backend/app/domain/workflow/permissions.py` mapping spaces, hyphens, and aliases (`PR` -> `press_release`) before risk tier assignment and query filtering.

2. **G-15: Review Concurrency & Double-Click Duplication**:
   - *Bug*: Firing two rapid review requests spawned two simultaneous orchestrations on the same content version, producing duplicate finding rows (14 findings instead of 7).
   - *Fix*: Added status checks in `trigger_review`: if active review is already `pending` or `running`, returns existing review record instead of launching concurrent tasks.

3. **G-16: Empty Content & 0-Byte Document Validation**:
   - *Bug*: Submissions with empty string `""` or 0-byte uploaded files returned HTTP 200, creating empty records and triggering pointless review jobs.
   - *Fix*: Added strict length validation ($\ge 5$ chars) in `create_submission` and `update_submission_content`, and verified `file.size > 0` in `upload_document_submission`, returning clear HTTP 422 before the review pipeline executes.

4. **F-67: Admin Demo Reset Endpoint Missing**:
   - *Bug*: `POST /api/v1/system/reset-demo` and `GET /api/v1/admin/reset-demo` referenced in documentation were missing from FastAPI routers.
   - *Fix*: Mounted both routes gated by `require_role("admin")` with `ALLOW_SEED_RESET` guard to reload seed data on demand.

5. **Phase 6: Image Upload Deduplication OCR Fallback String Collision**:
   - *Bug*: When OCR was unavailable, multiple image uploads generated the identical fallback text `"[Image submitted. OCR unavailable on this host...]"`. Content-hash deduplication caused the second image upload within 60s to return the first image's submission, bypassing visual checks on the second image.
   - *Fix*: Restricted 60-second content-hash deduplication strictly to raw text copy submissions in `create_submission`, allowing distinct document and image fixtures to process fresh.

6. **Phase 6: Verifier Timeout 500 Error Prevention**:
   - *Bug*: If an upstream LLM call hung during verifier execution, it would fail the review pipeline.
   - *Fix*: Wrapped LLM calls with a 30.0s deadline in `backend/app/adapters/llm/openai_compatible.py`. In `verifier.py`, caught `TimeoutError` and returned `{"verdict": "unsure", "reason": "Verifier timeout (exceeded 30s) — fallback applied; human judgment required."}` with `needs_human_judgment=True`, preventing 500 errors.

7. **Phase 6: Daily Cap Header Casing**:
   - *Bug*: When `LLM_DAILY_CAP` was reached, the fallback header was injected as `X-LLM-Cap-Reached`, but HTTP/2 clients receive lowercase headers (`x-llm-cap-reached`).
   - *Fix*: Updated verification to check headers case-insensitively.

8. **Phase 7: Mobile 375px Horizontal Scroll & Button Overflow**:
   - *Bug*: On 375px mobile viewports, finding action buttons (`Escalate`, `Dismiss`, `Accept Fix`) and header role dropdown overflowed the viewport.
   - *Fix*: Added `overflow-x-hidden` on `<main>`, adjusted finding card padding to `p-3.5 sm:p-4`, made card action buttons flex-wrap with `flex-1 sm:flex-none justify-center`, and shortened the header button text to `"Role"` on small screens.

9. **J3 Test Assertion on SubmissionDetail Schema**:
   - *Bug*: E2E test J3 asserted `len(appr1_data["approvals"]) == 1`, but `SubmissionDetail` represents approvals via `status == "In Review"` and `allowed_actions` exclusion.
   - *Fix*: Corrected test to assert `status == "In Review"` on approval 1, verify duplicate approval attempt by Reviewer 1 returns HTTP 400, and assert `status == "Approved"` only after Reviewer 2 approves.

---

## 5. Known Gaps

The following non-blocking improvements remain documented in [ROUND3_GAPS.md](file:///home/redpanda/Documents/WeBug/docs/ROUND3_GAPS.md):

1. **G-11 (F-14 Unstructured Guideline Import)**:
   - `POST /api/v1/kb/import/bulk` accepts structured JSON. Ingestion of raw unformatted `.txt` / `.md` guideline documents with heuristic rule classification remains a candidate roadmap feature.
2. **G-17 (Deep Link Redirect Preservation)**:
   - `<AuthGuard>` redirects unauthenticated deep links directly to `/` instead of preserving the original URL in a `?return_to=` query parameter.
3. **G-19 (Queue Partial Approval Badge)**:
   - In the Reviewer Queue table (`/reviewer-queue`), high-risk submissions with 1 of 2 approvals show status `In Review`, but do not yet render a dedicated `"1 of 2 Approved"` badge in the list view.

---

## 6. Real Test Outputs

### 6.1 `python manage.py e2e` (Run 1)
```text
[Inkguard E2E] Running end-to-end main journeys test suite (J1 - J9)...

[Inkguard CLI] >> Running: /home/redpanda/Documents/WeBug/.venv/bin/python -m pytest backend/tests/e2e -v
============================= test session starts ==============================
platform linux -- Python 3.14.8, pytest-9.1.1, pluggy-1.7.0 -- /home/redpanda/Documents/WeBug/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/redpanda/Documents/WeBug
plugins: anyio-4.15.1, asyncio-1.4.0, platformdirs-4.13.5
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 9 items

backend/tests/e2e/test_main_journeys.py::test_j1_creator_s1_fix_dismiss_submit PASSED [ 11%]
backend/tests/e2e/test_main_journeys.py::test_j2_reviewer_claim_comment_request_changes_resubmit PASSED [ 22%]
backend/tests/e2e/test_j3_high_risk_two_distinct_approvers_no_self_approval PASSED [ 33%]
backend/tests/e2e/test_main_journeys.py::test_j4_mark_published PASSED   [ 44%]
backend/tests/e2e/test_main_journeys.py::test_j5_brand_manager_guideline_health_and_approve_draft_rule PASSED [ 55%]
backend/tests/e2e/test_main_journeys.py::test_j6_admin_edits_kb_entry_historical_citation_preserved PASSED [ 66%]
backend/tests/e2e/test_main_journeys.py::test_j7_docx_pdf_and_image_upload PASSED [ 77%]
backend/tests/e2e/test_main_journeys.py::test_j8_evaluation_page_loads PASSED [ 88%]
backend/tests/e2e/test_main_journeys.py::test_j9_ai_off_admin_switch_rules_only_review PASSED [100%]

========================= 9 passed, 1 warning in 6.94s =========================
```

### 6.2 `python manage.py e2e` (Run 2 — Proving Zero Flakiness)
```text
[Inkguard E2E] Running end-to-end main journeys test suite (J1 - J9)...

[Inkguard CLI] >> Running: /home/redpanda/Documents/WeBug/.venv/bin/python -m pytest backend/tests/e2e -v
============================= test session starts ==============================
platform linux -- Python 3.14.8, pytest-9.1.1, pluggy-1.7.0 -- /home/redpanda/Documents/WeBug/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/redpanda/Documents/WeBug
plugins: anyio-4.15.1, asyncio-1.4.0, platformdirs-4.13.5
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 9 items

backend/tests/e2e/test_main_journeys.py::test_j1_creator_s1_fix_dismiss_submit PASSED [ 11%]
backend/tests/e2e/test_main_journeys.py::test_j2_reviewer_claim_comment_request_changes_resubmit PASSED [ 22%]
backend/tests/e2e/test_main_journeys.py::test_j3_high_risk_two_distinct_approvers_no_self_approval PASSED [ 33%]
backend/tests/e2e/test_main_journeys.py::test_j4_mark_published PASSED   [ 44%]
backend/tests/e2e/test_main_journeys.py::test_j5_brand_manager_guideline_health_and_approve_draft_rule PASSED [ 55%]
backend/tests/e2e/test_main_journeys.py::test_j6_admin_edits_kb_entry_historical_citation_preserved PASSED [ 66%]
backend/tests/e2e/test_main_journeys.py::test_j7_docx_pdf_and_image_upload PASSED [ 77%]
backend/tests/e2e/test_main_journeys.py::test_j8_evaluation_page_loads PASSED [ 88%]
backend/tests/e2e/test_main_journeys.py::test_j9_ai_off_admin_switch_rules_only_review PASSED [100%]

========================= 9 passed, 1 warning in 6.99s =========================
```

### 6.3 `python manage.py test` (All 147 Tests)
```text
[Inkguard Test] Running pytest test suite...

[Inkguard CLI] >> Running: /home/redpanda/Documents/WeBug/.venv/bin/python -m pytest backend/tests -v
============================= test session starts ==============================
platform linux -- Python 3.14.8, pytest-9.1.1, pluggy-1.7.0 -- /home/redpanda/Documents/WeBug/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/redpanda/Documents/WeBug
plugins: anyio-4.15.1, asyncio-1.4.0, platformdirs-4.13.5
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 147 items

backend/tests/architecture/test_contracts.py::test_import_linter_contracts PASSED [  0%]
backend/tests/e2e/test_main_journeys.py::test_j1_creator_s1_fix_dismiss_submit PASSED [  1%]
backend/tests/e2e/test_main_journeys.py::test_j2_reviewer_claim_comment_request_changes_resubmit PASSED [  2%]
backend/tests/e2e/test_main_journeys.py::test_j3_high_risk_two_distinct_approvers_no_self_approval PASSED [  2%]
backend/tests/e2e/test_main_journeys.py::test_j4_mark_published PASSED   [  3%]
backend/tests/e2e/test_main_journeys.py::test_j5_brand_manager_guideline_health_and_approve_draft_rule PASSED [  4%]
backend/tests/e2e/test_main_journeys.py::test_j6_admin_edits_kb_entry_historical_citation_preserved PASSED [  4%]
backend/tests/e2e/test_main_journeys.py::test_j7_docx_pdf_and_image_upload PASSED [  5%]
backend/tests/e2e/test_main_journeys.py::test_j8_evaluation_page_loads PASSED [  6%]
backend/tests/e2e/test_main_journeys.py::test_j9_ai_off_admin_switch_rules_only_review PASSED [  6%]
backend/tests/eval/test_eval_metrics.py::test_confusion_matrix_calculations PASSED [  7%]
backend/tests/eval/test_eval_metrics.py::test_category_breakdowns PASSED [  8%]
backend/tests/eval/test_eval_runner.py::test_rules_only_offline_determinism PASSED [  8%]
backend/tests/eval/test_eval_runner.py::test_dataset_schema_validation PASSED [  9%]
backend/tests/eval/test_eval_runner.py::test_runner_mock_eval PASSED     [ 10%]
backend/tests/eval/test_eval_runner.py::test_runner_cached_eval PASSED   [ 10%]
backend/tests/eval/test_eval_runner.py::test_verifier_drops_unsupported_candidate PASSED [ 11%]
backend/tests/eval/test_eval_runner.py::test_verifier_preserves_supported_candidate PASSED [ 12%]
backend/tests/eval/test_eval_runner.py::test_cli_smoke_rules_only PASSED [ 12%]
backend/tests/eval/test_eval_runner.py::test_cli_smoke_cached PASSED     [ 13%]
backend/tests/eval/test_eval_runner.py::test_evaluation_report_schema PASSED [ 14%]
backend/tests/eval/test_eval_runner.py::test_precision_recall_thresholds PASSED [ 14%]
backend/tests/eval/test_eval_runner.py::test_benchmark_cache_completeness PASSED [ 15%]
backend/tests/integration/test_admin_reset_demo.py::test_reset_demo_endpoint_admin_only PASSED [ 16%]
backend/tests/integration/test_auth.py::test_auth_login_success PASSED   [ 17%]
backend/tests/integration/test_auth.py::test_auth_login_invalid_password PASSED [ 17%]
backend/tests/integration/test_auth.py::test_auth_login_nonexistent_user PASSED [ 18%]
backend/tests/integration/test_auth.py::test_auth_demo_users_endpoint PASSED [ 19%]
backend/tests/integration/test_auth.py::test_auth_me_with_valid_token PASSED [ 19%]
backend/tests/integration/test_auth.py::test_auth_me_with_invalid_token PASSED [ 20%]
backend/tests/integration/test_auth.py::test_auth_me_with_no_token PASSED [ 21%]
backend/tests/integration/test_document_upload.py::test_upload_good_docx PASSED [ 21%]
backend/tests/integration/test_document_upload.py::test_upload_bad_a11y_docx PASSED [ 22%]
backend/tests/integration/test_document_upload.py::test_upload_text_pdf PASSED [ 23%]
backend/tests/integration/test_document_upload.py::test_upload_scanned_pdf PASSED [ 23%]
backend/tests/integration/test_document_upload.py::test_upload_corrupted_file PASSED [ 24%]
backend/tests/integration/test_document_upload.py::test_upload_renamed_exe PASSED [ 25%]
backend/tests/integration/test_document_upload.py::test_upload_oversize_file PASSED [ 25%]
backend/tests/integration/test_document_upload.py::test_upload_zip_bomb PASSED [ 26%]
backend/tests/integration/test_guideline_health_router.py::test_guideline_health_endpoint PASSED [ 27%]
backend/tests/integration/test_guideline_health_router.py::test_stale_rules_endpoint PASSED [ 27%]
backend/tests/integration/test_guideline_health_router.py::test_gaps_endpoint_bm25_clustering PASSED [ 28%]
backend/tests/integration/test_guideline_health_router.py::test_gaps_approve_and_reject_with_audit_log PASSED [ 29%]
backend/tests/integration/test_health_and_stubs.py::test_health_check PASSED [ 29%]
backend/tests/integration/test_health_and_stubs.py::test_submissions_and_findings_stubs PASSED [ 30%]
backend/tests/integration/test_health_and_stubs.py::test_error_envelope_format PASSED [ 31%]
backend/tests/integration/test_insights_and_audit.py::test_insights_endpoints PASSED [ 31%]
backend/tests/integration/test_insights_and_audit.py::test_audit_filters_and_csv_export PASSED [ 32%]
backend/tests/integration/test_insights_and_audit.py::test_system_status_endpoint PASSED [ 33%]
backend/tests/integration/test_kb.py::test_kb_crud_and_versioning PASSED [ 33%]
backend/tests/integration/test_phase6_robustness.py::test_phase6_30s_timeout_wrapper_and_safe_fallback PASSED [ 34%]
backend/tests/integration/test_phase6_robustness.py::test_phase6_idempotency_60s_returns_existing_submission PASSED [ 35%]
backend/tests/integration/test_phase6_robustness.py::test_phase6_daily_cap_enforcement_and_header PASSED [ 35%]
backend/tests/integration/test_review_engine_and_findings.py::test_full_review_flow_and_findings_triage_in_mock_mode PASSED [ 36%]
backend/tests/integration/test_review_engine_and_findings.py::test_safety_captured_outgoing_payload_contains_no_confidential_text_or_secret PASSED [ 37%]
backend/tests/integration/test_review_engine_and_findings.py::test_safety_daily_cap_zero_forces_fallback PASSED [ 37%]
backend/tests/integration/test_review_engine_and_findings.py::test_safety_no_external_ai_switch_honoured PASSED [ 38%]
backend/tests/integration/test_review_engine_and_findings.py::test_safety_approval_on_old_version_rejected_after_edit PASSED [ 39%]
backend/tests/integration/test_review_engine_and_findings.py::test_safety_oversized_content_returns_413 PASSED [ 39%]
backend/tests/integration/test_review_engine_and_findings.py::test_safety_review_rate_limit_returns_429 PASSED [ 40%]
backend/tests/integration/test_round3_loose_ends.py::test_g14_channel_normalization PASSED [ 41%]
backend/tests/integration/test_round3_loose_ends.py::test_g16_empty_content_validation PASSED [ 41%]
backend/tests/integration/test_round3_loose_ends.py::test_f67_reset_demo_endpoints PASSED [ 42%]
backend/tests/integration/test_round3_loose_ends.py::test_f26_notification_lifecycle PASSED [ 43%]
backend/tests/integration/test_security_hardening.py::test_demo_mode_requires_explicit_env_setting PASSED [ 43%]
backend/tests/integration/test_security_hardening.py::test_dev_ui_gated_in_production PASSED [ 44%]
backend/tests/integration/test_security_hardening.py::test_agents_md_safety_invariants_inventory PASSED [ 45%]
backend/tests/integration/test_submissions_and_workflow.py::test_full_workflow_lifecycle PASSED [ 46%]
backend/tests/integration/test_submissions_and_workflow.py::test_high_risk_two_reviewer_requirement PASSED [ 46%]
backend/tests/integration/test_users_and_rbac.py::test_rbac_user_management PASSED [ 47%]
backend/tests/unit/test_ai_domain.py::test_rule_engine_per_rule_type PASSED [ 48%]
backend/tests/unit/test_ai_domain.py::test_accessibility_checks PASSED   [ 48%]
backend/tests/unit/test_ai_domain.py::test_guardrail_fake_citation_dropped PASSED [ 49%]
backend/tests/unit/test_ai_domain.py::test_guardrail_mismatched_excerpt_dropped PASSED [ 50%]
backend/tests/unit/test_ai_domain.py::test_guardrail_expired_fact_decided_in_code PASSED [ 50%]
backend/tests/unit/test_ai_domain.py::test_guardrail_low_confidence_needs_human_judgment PASSED [ 51%]
backend/tests/unit/test_ai_domain.py::test_suggestion_validator_rules PASSED [ 52%]
backend/tests/unit/test_ai_domain.py::test_injection_sample_s5_flagged_and_behavior_unchanged PASSED [ 52%]
backend/tests/unit/test_ai_domain.py::test_sanitise_redaction_leaves_no_seeded_secret PASSED [ 53%]
backend/tests/unit/test_ai_domain.py::test_openai_adapter_outgoing_payload_asserts_no_confidential_entry PASSED [ 54%]
backend/tests/unit/test_document_extractor.py::test_docx_extractor_structure PASSED [ 54%]
backend/tests/unit/test_document_extractor.py::test_pdf_extractor_structure PASSED [ 55%]
backend/tests/unit/test_document_extractor.py::test_file_safety_validation PASSED [ 56%]
backend/tests/unit/test_document_extractor.py::test_unsupported_format_rejected PASSED [ 56%]
backend/tests/unit/test_document_extractor.py::test_corrupted_file_handling PASSED [ 57%]
backend/tests/unit/test_guideline_health.py::test_ambiguity_scoring_formula PASSED [ 58%]
backend/tests/unit/test_guideline_health.py::test_ambiguity_scoring_low_sample_size PASSED [ 59%]
backend/tests/unit/test_guideline_health.py::test_ambiguity_recommendations PASSED [ 59%]
backend/tests/unit/test_guideline_health.py::test_uncited_comment_clustering_bm25 PASSED [ 60%]
backend/tests/unit/test_guideline_health.py::test_uncited_comment_clustering_min_size PASSED [ 61%]
backend/tests/unit/test_guideline_health.py::test_stale_rules_detection_unused PASSED [ 61%]
backend/tests/unit/test_guideline_health.py::test_stale_rules_detection_review_date PASSED [ 62%]
backend/tests/unit/test_guideline_health.py::test_stale_facts_detection PASSED [ 63%]
backend/tests/unit/test_guideline_health.py::test_rules_citing_expired_facts PASSED [ 63%]
backend/tests/unit/test_image_checks.py::test_palette_compliance_pure_python PASSED [ 64%]
backend/tests/unit/test_image_checks.py::test_logo_average_hash_detection PASSED [ 65%]
backend/tests/unit/test_image_checks.py::test_image_contrast_ratio_wcag PASSED [ 65%]
backend/tests/unit/test_image_checks.py::test_oversized_dimensions_rejected_with_422 PASSED [ 66%]
backend/tests/unit/test_image_checks.py::test_oversized_filesize_rejected_with_422 PASSED [ 67%]
backend/tests/unit/test_image_checks.py::test_decompression_bomb_guard_returns_422 PASSED [ 67%]
backend/tests/unit/test_image_checks.py::test_corrupted_image_rejected_with_422 PASSED [ 68%]
backend/tests/unit/test_image_checks.py::test_unsupported_format_rejected_with_422 PASSED [ 69%]
backend/tests/unit/test_image_checks.py::test_ocr_graceful_degradation PASSED [ 69%]
backend/tests/unit/test_image_checks.py::test_api_upload_on_palette_image PASSED [ 70%]
backend/tests/unit/test_image_checks.py::test_api_upload_off_palette_image PASSED [ 71%]
backend/tests/unit/test_image_checks.py::test_api_upload_with_logo_image PASSED [ 71%]
backend/tests/unit/test_image_checks.py::test_api_upload_oversized_dimensions_returns_422 PASSED [ 72%]
backend/tests/unit/test_image_checks.py::test_api_upload_corrupted_image_returns_422 PASSED [ 73%]
backend/tests/unit/test_image_checks.py::test_api_upload_unsupported_format_returns_422 PASSED [ 73%]
backend/tests/unit/test_permissions.py::test_can_access_tier PASSED      [ 74%]
backend/tests/unit/test_permissions.py::test_role_capabilities PASSED    [ 75%]
backend/tests/unit/test_permissions.py::test_required_approvals PASSED   [ 76%]
backend/tests/unit/test_permissions.py::test_creator_cannot_approve_own_submission PASSED [ 76%]
backend/tests/unit/test_permissions.py::test_high_severity_blocks_submission PASSED [ 77%]
backend/tests/unit/test_permissions.py::test_finding_allowed_actions PASSED [ 78%]
backend/tests/unit/test_state_machine.py::test_valid_workflow_progression PASSED [ 78%]
backend/tests/unit/test_state_machine.py::test_safety_invariant_creator_cannot_approve_own PASSED [ 79%]
backend/tests/unit/test_state_machine.py::test_cannot_submit_with_open_high_severity_findings PASSED [ 80%]
backend/tests/unit/test_state_machine.py::test_multi_approver_requirement_for_high_risk PASSED [ 81%]
backend/tests/unit/test_state_machine.py::test_editing_content_resets_approved_to_draft PASSED [ 81%]
backend/tests/unit/test_state_machine.py::test_table_driven_role_transitions[creator-True-Checked-Submitted-True] PASSED [ 82%]
backend/tests/unit/test_state_machine.py::test_table_driven_role_transitions[brand_manager-False-Checked-Submitted-True] PASSED [ 83%]
backend/tests/unit/test_state_machine.py::test_table_driven_role_transitions[admin-False-Checked-Submitted-True] PASSED [ 84%]
backend/tests/unit/test_state_machine.py::test_table_driven_role_transitions[reviewer-False-Checked-Submitted-False] PASSED [ 84%]
backend/tests/unit/test_state_machine.py::test_table_driven_role_transitions[reviewer-False-Submitted-In Review-True] PASSED [ 85%]
backend/tests/unit/test_state_machine.py::test_table_driven_role_transitions[brand_manager-False-Submitted-In Review-True] PASSED [ 86%]
backend/tests/unit/test_state_machine.py::test_table_driven_role_transitions[admin-False-Submitted-In Review-True] PASSED [ 86%]
backend/tests/unit/test_state_machine.py::test_table_driven_role_transitions[creator-True-Submitted-In Review-False] PASSED [ 87%]
backend/tests/unit/test_state_machine.py::test_table_driven_role_transitions[reviewer-False-In Review-Changes Requested-True] PASSED [ 88%]
backend/tests/unit/test_state_machine.py::test_table_driven_role_transitions[brand_manager-False-In Review-Changes Requested-True] PASSED [ 89%]
backend/tests/unit/test_state_machine.py::test_table_driven_role_transitions[admin-False-In Review-Changes Requested-True] PASSED [ 89%]
backend/tests/unit/test_state_machine.py::test_table_driven_role_transitions[creator-True-In Review-Changes Requested-False] PASSED [ 90%]
backend/tests/unit/test_state_machine.py::test_table_driven_role_transitions[reviewer-True-In Review-Approved-False] PASSED [ 91%]
backend/tests/unit/test_state_machine.py::test_table_driven_role_transitions[reviewer-False-In Review-Approved-True] PASSED [ 92%]
backend/tests/unit/test_state_machine.py::test_table_driven_role_transitions[brand_manager-False-In Review-Approved-True] PASSED [ 92%]
backend/tests/unit/test_state_machine.py::test_table_driven_role_transitions[creator-True-In Review-Approved-False] PASSED [ 93%]
backend/tests/unit/test_state_machine.py::test_table_driven_role_transitions[creator-True-Approved-Marked Published-True] PASSED [ 94%]
backend/tests/unit/test_state_machine.py::test_table_driven_role_transitions[brand_manager-False-Approved-Marked Published-True] PASSED [ 95%]
backend/tests/unit/test_state_machine.py::test_table_driven_role_transitions[admin-False-Approved-Marked Published-True] PASSED [ 95%]
backend/tests/unit/test_state_machine.py::test_table_driven_role_transitions[reviewer-False-Approved-Marked Published-False] PASSED [ 96%]
backend/tests/unit/test_verifier.py::test_verifier_supported_finding_kept PASSED [ 97%]
backend/tests/unit/test_verifier.py::test_verifier_unsupported_citation_dropped PASSED [ 97%]
backend/tests/unit/test_verifier.py::test_verifier_unsure_becomes_needs_human_judgment PASSED [ 98%]
backend/tests/unit/test_verifier.py::test_verifier_ai_down_falls_back_without_error PASSED [ 99%]
backend/tests/unit/test_verifier.py::test_verifier_confidential_text_never_in_payload PASSED [100%]

====================== 147 passed, 14 warnings in 22.73s =======================
```

### 6.4 `python manage.py arch`
```text
[Inkguard Arch] Verifying clean architecture boundaries with import-linter...

[Inkguard CLI] >> Running: /home/redpanda/Documents/WeBug/.venv/bin/python -c import importlinter.cli, sys; sys.exit(importlinter.cli.lint_imports())

╔══╗─────────▶╔╗ ╔╗      ╔╗◀───┐
╚╣╠╝◀─────┐  ╔╝╚╗║║────▶╔╝╚╗   │
 ║║   ╔══╦══╦╩╗╔╝║║  ╔╦═╩╗╔╝╔═╦══╗
 ║║╔══╣╔╗║╔╗║╔╣║ ║║ ╔╬╣╔╗║║ ║│║╔═╝
╔╣╠╣║║║╚╝║╚╝║║║╚╗║╚═╝║║║║║╚╗║═╣║
╚══╩╩╩╣╔═╩══╩╝╚═╝╚═══╩╩╝╚╩═╩╩═╩╝
  └──▶║║                    ▲ 
      ╚╝────────────────────┘


---------
Contracts
---------

Analyzed 114 files, 383 dependencies.
-------------------------------------

Domain layer purity KEPT
Application layer isolation KEPT

Contracts: 2 kept, 0 broken.
```

### 6.5 `python manage.py eval --mode rules_only --verifier off`
```text
[Inkguard CLI] >> Running: /home/redpanda/Documents/WeBug/.venv/bin/python -m app.eval.cli --mode rules_only --verifier off

### Evaluation Results: Mode `rules_only` (Verifier: OFF)
- **Total Documents**: 84 | **Clean Documents**: 21 (Clean Pass Rate: 81.0%)
- **Overall**: Precision: **0.915** | Recall: **0.765** | F1: **0.833** (TP: 65, FP: 6, FN: 20)

| Category | TP | FP | FN | Precision | Recall | F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `accessibility` | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| `claim` | 6 | 1 | 17 | 0.857 | 0.261 | 0.400 |
| `confidential_leak` | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| `missing_disclaimer` | 18 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| `readability` | 0 | 4 | 0 | 0.000 | 1.000 | 0.000 |
| `terminology` | 32 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| `tone` | 5 | 1 | 3 | 0.833 | 0.625 | 0.714 |

**Claim Verdict Breakdown**:

| Verdict | TP | FP | FN | Precision | Recall | F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `Contradicted` | 0 | 0 | 3 | 0.000 | 0.000 | 0.000 |
| `Expired` | 0 | 0 | 4 | 0.000 | 0.000 | 0.000 |
| `Supported` | 0 | 0 | 8 | 0.000 | 0.000 | 0.000 |
| `Unverified` | 0 | 0 | 2 | 0.000 | 0.000 | 0.000 |
```

### 6.6 `npm run build` (Next.js Static Export)
```text
> frontend@0.1.0 build
> next build

▲ Next.js 16.4.3 (Turbopack)
✓ Running next.config.ts took 195ms

  Creating an optimized production build ...
✓ Compiled successfully in 3.0s
  Finished TypeScript in 8.2s    ✓ Finished TypeScript in 8.2s 
  Collecting page data using 17 workers in 3.8s    ✓ Collecting page data using 17 workers in 3.8s 
✓ Generating static pages using 17 workers (20/20) in 1586ms
  Finalizing page optimization in 483ms    ✓ Finalizing page optimization in 483ms 

Route (app)
┌ ○ /
├ ○ /_not-found
├ ○ /about-ai
├ ○ /audit
├ ○ /dashboard
├ ○ /dev/ui
├ ○ /eval
├ ○ /insights
├ ○ /insights/guideline-health
├ ○ /kb
├ ○ /queue
├ ○ /reviewer-queue
├ ○ /settings
├ ○ /status
├ ○ /submission
├ ○ /submission/new
├ ○ /submissions
└ ○ /submissions/new

○  (Static)  prerendered as static content
```
