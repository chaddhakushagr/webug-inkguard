# Data Model Specification

Inkguard uses database-agnostic SQLAlchemy models with UUID strings, UTC timezone-aware timestamps, and generic JSON columns.

## Core Entities
1. **teams**: id, name, created_at
2. **users**: id, email, name, password_hash, role, max_tier, team_id, is_active, created_at
3. **kb_entries**: id, code (e.g. FACT-003, unique), type (term, fact, tone, rule, asset), title, body, data (JSON), classification (public, internal, confidential), owner_id, status (active, retired), current_version, created_at
4. **kb_entry_versions**: id, entry_id, version, snapshot (JSON), changed_by, change_note, created_at (immutable)
5. **submissions**: id, title, channel, risk_tier, status, creator_id, team_id, current_version_id, assignee_id, published_url, published_at, is_synthetic, created_at, updated_at
6. **submission_versions**: id, submission_id, version_no, content, content_hash, created_by, source, parent_version_id, created_at
7. **reviews**: id, submission_version_id, status, mode, provider, model, prompt_version, kb_snapshot (JSON), kb_snapshot_hash, redaction_log (JSON), stats (JSON), error, started_at, finished_at
8. **findings**: id, review_id, submission_version_id, fingerprint, source (rule/ai), issue_type, severity, confidence, span_start, span_end, excerpt, cited_entry_id, cited_entry_version, claim_verdict, is_policy, needs_human_judgment, explanation, suggested_fix, status (open, accepted, dismissed, escalated), is_synthetic, created_at
9. **finding_actions**: id, finding_id, actor_id, action, reason_code, reason_text, created_at
10. **comments**: id, submission_id, finding_id, parent_id, author_id, body, created_at
11. **approvals**: id, submission_id, version_id, reviewer_id, decision, note, voided, created_at
12. **audit_log**: id, ts, actor_id, actor_role, action, entity_type, entity_id, details (JSON), request_id, prev_hash, hash (append-only)
13. **ai_calls**: id, review_id, purpose, provider, model, chars_sent, redaction_summary (JSON), kb_entry_ids (JSON), max_tier_sent, status, latency_ms, tokens_in, tokens_out, cache_hit, created_at
14. **llm_cache**: key (PK), response (JSON), created_at
15. **settings**: key (PK), value (JSON), updated_at
