# Security & Privacy Policy

## Invariants & Implementation Evidence

1. **Classification Tier Isolation**:
   - Pure domain enforcement: `app.domain.workflow.permissions.can_access_tier(user_tier, entry_tier)`
   - API layer: `/api/v1/kb/entries` strictly filters entries where caller's `max_tier` is insufficient. Unauthorized entries return 404.
   - Tested by: `test_can_access_tier`, `test_kb_crud_and_versioning`.

2. **Confidential Egress Boundary**:
   - Confidential entries are hard-filtered in `BM25Retriever.retrieve`.
   - The LLM adapter `OpenAICompatibleLLMAdapter._prepare_payload` raises a `ValueError` if any confidential entry is present.
   - Tested by: `test_openai_adapter_outgoing_payload_asserts_no_confidential_entry`.

3. **PII and Secret Redaction**:
   - `SanitiseStage` scans for emails, telephone numbers, API keys (`sk-*`, `AIza*`, `ghp_*`, `AKIA*`), and known confidential codenames ("Project Lumina").
   - Redacted tokens (`[EMAIL_REDACTED_N]`, `[SECRET_REDACTED_N]`, etc.) replace sensitive strings.
   - Placeholder map is kept in ephemeral process memory. Raw secret text is never written to logs or sent over the wire.
   - Tested by: `test_sanitise_redaction_leaves_no_seeded_secret`.

4. **Prompt Injection Hardening**:
   - Prompts in `backend/app/prompts/` isolate user copy inside `<<<CONTENT_DATA>>>` and `<<</CONTENT_DATA>>>` delimiters with explicit instructions that content between delimiters is untrusted user data.
   - `SanitiseStage` flags prompt injection attempts (e.g. `ignore previous instructions`, `system override`) and records `prompt_injection_flagged` without crashing or altering brand rule evaluation.
   - Tested by: `test_injection_sample_s5_flagged_and_behavior_unchanged`.

5. **Cryptographic Append-Only Audit Trail**:
   - Every state change, login, KB edit, review run, and finding action writes an immutable record to `audit_log`.
   - Hash chaining: `hash = sha256(prev_hash | ts | actor | action | entity_type | entity_id | details)`.
   - Immutability guards: SQLAlchemy event listeners block `UPDATE` and `DELETE` with `RuntimeError`. An Alembic migration provisions a PostgreSQL database trigger on Postgres deployments.
   - Tested by: `test_audit_hash_chaining_and_immutability`.

6. **Self-Approval Prohibition**:
   - Pure domain workflow invariant: `is_creator` cannot approve own submission (`WorkflowStateMachine.validate_transition` raises `PermissionDeniedError`).
   - Tested by: `test_creator_cannot_approve_own_submission`, `test_full_workflow_lifecycle`.

7. **Multi-Approver Requirement for High-Risk Channels**:
   - Submissions on `press_release` channel automatically inherit `risk_tier = "high"`.
   - Requires 2 distinct reviewer approvals before transitioning to `Approved`.
   - Tested by: `test_high_risk_two_reviewer_requirement`, `test_multi_approver_requirement_for_high_risk`.
