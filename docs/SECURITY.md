# Security Policy, Audits & Invariants Log

**Last Verified:** Sat 24 Oct 2026, 22:45 IST  
**Audit Status:** 0 Vulnerabilities Found (0 Critical, 0 High, 0 Medium, 0 Low)

---

## 1. Automated Dependency Audits

### Python Backend (`pip-audit`)
- **Command:** `pip-audit -r backend/requirements.txt` and `pip-audit` (full virtualenv scan)
- **Tool Version:** `pip-audit v2.10.1` (querying PyPI Advisory Database via OSV)
- **Result:**
  ```text
  No known vulnerabilities found
  ```
- **Vulnerabilities Found:** 0

### Frontend (`npm audit`)
- **Command:** `npm audit --prefix frontend`
- **Result:**
  ```text
  found 0 vulnerabilities
  ```
- **Vulnerabilities Found:** 0

---

## 2. AGENTS.md Section 3: Safety Invariants & Automated Test Mapping

Every safety invariant defined in `AGENTS.md` section 3 is backed by automated tests:

| Invariant | Requirement | Automated Test Names | Test File |
|---|---|---|---|
| **1. Suggest, never act** | No code path lets AI approve, publish, accept a fix or overwrite content. Only an authenticated human request changes state. Creators can never approve their own submission. | `test_creator_cannot_approve_own_submission`, `test_safety_invariant_creator_cannot_approve_own`, `test_full_workflow_lifecycle` | `backend/tests/unit/test_permissions.py`, `backend/tests/unit/test_state_machine.py`, `backend/tests/integration/test_submissions_and_workflow.py` |
| **2. Confidential entries egress boundary** | Confidential entries never reach an external model. Tier filtering occurs in retriever and LLM adapter. Outgoing payload is captured and asserted free of secrets and confidential text. | `test_safety_captured_outgoing_payload_contains_no_confidential_text_or_secret`, `test_openai_adapter_outgoing_payload_asserts_no_confidential_entry`, `test_sanitise_redaction_leaves_no_seeded_secret` | `backend/tests/integration/test_review_engine_and_findings.py`, `backend/tests/unit/test_ai_domain.py` |
| **3. No citation, no policy finding** | The LLM may only cite entry codes it was provided. Hallucinated citations and mismatched text excerpts are dropped by code-level guardrails. | `test_guardrail_fake_citation_dropped`, `test_guardrail_mismatched_excerpt_dropped` | `backend/tests/unit/test_ai_domain.py` |
| **4. Expired decided by code** | Expiry is evaluated strictly by code from `valid_until`, never by the LLM. | `test_guardrail_expired_fact_decided_in_code` | `backend/tests/unit/test_ai_domain.py` |
| **5. Untrusted input** | Submitted copy is wrapped inside delimiters (`<<<CONTENT_DATA>>>`), validated against strict Pydantic schemas, and injection phrases are flagged without behavior alteration. | `test_injection_sample_s5_flagged_and_behavior_unchanged`, `test_suggestion_validator_rules` | `backend/tests/unit/test_ai_domain.py` |
| **6. Audit log is append-only** | Append-only ledger with cryptographic SHA-256 hash chaining. Immutability enforced by application listeners and PostgreSQL database trigger. | `test_audit_hash_chaining_and_immutability`, `test_audit_filters_and_csv_export` | `backend/tests/integration/test_audit_immutability.py`, `backend/tests/integration/test_insights_and_audit.py` |
| **7. Graceful degradation** | When external AI is unavailable, capped, or switched off via admin emergency switch, rule-based checks and the full editorial workflow continue to function. | `test_safety_no_external_ai_switch_honoured`, `test_full_review_flow_and_findings_triage_in_mock_mode` | `backend/tests/integration/test_review_engine_and_findings.py` |
| **8. Daily cap on live LLM calls** | Daily call cap stored in settings automatically forces fallback to `rules_only` when reached or when set to 0. | `test_safety_daily_cap_zero_forces_fallback` | `backend/tests/integration/test_review_engine_and_findings.py` |
| **9. Disclosure** | AI badge rendered on all AI-generated suggestions, rule findings visually distinct (solid vs wavy underline), data boundary panel available for every review. | `test_full_review_flow_and_findings_triage_in_mock_mode` | `backend/tests/integration/test_review_engine_and_findings.py` |

---

## 3. Configuration & Route Hardening

### DEMO_MODE Safeguards
- In `backend/app/config.py`, `DEMO_MODE` defaults strictly to `False`.
- `DEMO_MODE` cannot be enabled in production config unless explicitly passed as `DEMO_MODE=true` in the host's environment variables.
- Verified by: `test_demo_mode_requires_explicit_env_setting` in `backend/tests/integration/test_security_hardening.py`.

### `/dev/ui` Route Gating
- When `APP_ENV=production`, requests to `/dev` or `/dev/ui/` are intercepted by middleware and return `HTTP 404 Not Found` with a standardized error envelope.
- In `APP_ENV=development`, `/dev/ui/` is accessible for UI component preview.
- Verified by: `test_dev_ui_gated_in_production` in `backend/tests/integration/test_security_hardening.py`.

### Secret Scans
- Git working tree: `git grep -E "(AIza[0-9A-Za-z_-]{35}|sk-[a-zA-Z0-9]{20,})"` -> 0 matches.
- Git commit history: `git log -p | grep -E "(AIza[0-9A-Za-z_-]{35}|sk-[a-zA-Z0-9]{20,})"` -> 0 matches.
- Secret keys: `git grep -i "SECRET_KEY="` -> 0 matches.
- `.env` is listed in `.gitignore` and `.dockerignore`.
