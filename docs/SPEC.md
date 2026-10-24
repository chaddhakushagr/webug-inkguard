# Inkguard: build specification (Round 2)

Round 2 judging (100): working core workflow 30, technical depth and reliability 25, progress from Round 1 20, three planned Round 3 improvements 15, usability 10. A judge must open the public link and use the core product with no help.

## 1. Product and principles

Content goes in. Findings come out, each with a type, severity, plain-language explanation, the cited approved source (with version) and a suggested fix. Humans accept, dismiss or escalate. Reviewers comment, approve or request changes. Every step is logged. Over time the product shows recurring mistakes and which rules look unclear.

1. Verification, not generation: retrieve the relevant rules and facts, then check the content against them.
2. Deterministic first, AI second: exact checks in code, LLM only for tone and claim reasoning.
3. No citation, no policy finding.
4. Suggest, never act. The system never publishes.
5. Abstain when unsure ("needs human judgment").
6. Record everything: model, prompt version, knowledge-base versions, what left the boundary.
7. Claim verdicts: Supported, Contradicted, Unverified, Expired.

## 2. Roles and permissions

Roles: `creator`, `reviewer`, `brand_manager`, `admin`. Users have a `team` and a `max_tier` (public, internal, confidential). An agency writer is a creator with `max_tier = public`. Defaults: admin and brand_manager = confidential, reviewer and creator = internal.

| Capability | creator | reviewer | brand_manager | admin |
|---|---|---|---|---|
| Create, edit, run review, act on findings, submit (own, while Draft or Changes Requested) | yes | no | own | own |
| Claim, comment, approve, request changes | comment on own | yes | yes | yes |
| Approve own submission | never | n/a | never | never |
| Mark published | own | no | yes | yes |
| View knowledge base | up to own tier | up to own tier | up to own tier | all |
| Edit knowledge base | no | no | yes | yes |
| Insights | own team | yes | yes | yes |
| Audit log, risk-tier config | no | no | yes | yes |
| Users and settings (egress policy, AI switch, daily cap) | no | no | no | yes |

Enforce on the server only. The UI uses `allowed_actions` returned by the API.

## 3. Features (tier M = must ship, S = should, C = could)

| ID | Feature | Tier |
|---|---|---|
| F-01 | Email and password login, JWT with short expiry, hashed passwords, `/auth/me` | M |
| F-02 | One-click demo login per role (DEMO_MODE) and a "synthetic demo data" banner | M |
| F-03 | Server-side RBAC, tier filtering, `allowed_actions` | M |
| F-04 | User management by admin | C |
| F-05 | Teams | M |
| F-10 | Knowledge-base entries: term, fact, tone, rule, asset (metadata). Create, edit, retire | M |
| F-11 | Immutable versions, history view, reviews record versions used | M |
| F-12 | Classification tiers on every entry | M |
| F-13 | Fact validity dates, "expiring soon" and "expired" badges | M |
| F-14 | Guideline document import (.txt/.md to candidate entries, heuristic, human confirms) | C |
| F-15 | Terminology: banned, preferred, match type, severity, reason, exceptions | M |
| F-16 | Bulk JSON import and the seed loader | M |
| F-20 | Create submission: title, channel, pasted text, auto risk tier | M |
| F-21 | Content versions with inline diff | M |
| F-22 | State machine (section 7) with 409 on invalid transitions | M |
| F-23 | Risk tiers and approvals (1 approver low and medium, 2 high), no self-approval, edits void approvals | M |
| F-24 | Threaded comments on submission and on a finding | M |
| F-25 | Reviewer queue with claim | M |
| F-26 | In-app notifications | C |
| F-27 | Mark Published by a human, optional URL | M |
| F-28 | Append-only hash-chained audit log with filterable UI | M |
| F-29 | Role-specific dashboard | M |
| F-30 | Review orchestration as a background job with polled progress | M |
| F-31 | Sanitise and redact before any external call, redaction log (type and count only) | M |
| F-32 | Prompt-injection hardening and flagging | M |
| F-33 | Rule checks: terms, disclaimers, regex rules, claim triggers, confidential-term leak | M |
| F-34 | Text accessibility and readability: reading grade, very long sentences, ALL-CAPS runs, "click here" links, markdown images without alt text, heading skips | M |
| F-35 | Retrieval: in-process BM25 over the (small) knowledge base, filtered by tier and egress policy | M |
| F-36 | LLM analysis returning strict JSON (claims with verdicts, tone per attribute, notes) | M |
| F-37 | Guardrails in code (section 8 step 6) | M |
| F-38 | Minimal-edit suggestions with a change cap and validators | M |
| F-39 | LLM adapter for any OpenAI-compatible endpoint with modes `live`, `cached`, `mock`, `rules_only` | M |
| F-40 | Response cache (database table) and `warm-cache` command | M |
| F-41 | Data-boundary log per external call | M |
| F-42 | Versioned prompt files, version stored on each review | M |
| F-43 | Findings model | M |
| F-44 | Finding actions: accept (new content version), dismiss (reason required), escalate | M |
| F-45 | Re-check carrying over dismissed findings by fingerprint | C |
| F-46 | Highlighted findings in the content, click to focus, keyboard operable | M |
| F-50 | Recurring issues by type, rule, team, week | M |
| F-51 | Dismissal and override reasons breakdown | M |
| F-52 | Per-rule raw counters (no scoring; scoring is Round 3) | S |
| F-53 | Synthetic history seed, labelled synthetic in the UI | M |
| F-60 | AI-disclosure badge and "About AI" page | M |
| F-61 | Rule findings and AI findings visually distinct | M |
| F-62 | Data-boundary panel on the review screen | M |
| F-63 | Admin egress policy and "no external AI" switch | M |
| F-64 | Security basics (section 11) | M |
| F-66 | Daily cap on live LLM calls with automatic fallback and banner | M |
| F-67 | Admin "reset demo data" | C |
| F-70 | First-run guide, 5 one-click sample submissions, empty states | M |
| F-71 | Accessible, responsive UI (keyboard, labels, focus, 4.5:1 contrast, not colour alone) | M |
| F-72 | Loading, empty and error states everywhere | M |
| F-73 | Status page: version, AI mode, health | S |
| F-80 | Tests: domain unit, API integration, golden-path e2e script | M |
| F-82 | Local run via `python manage.py` (no make, no Docker) | M |
| F-83 | Health endpoint, request ids, structured logs, optional keep-alive workflow | S |
| F-85 | Architecture tests with import-linter | M |
| F-86 | Free-cloud deployment (section 14) | M |

## 4. Architecture

```
frontend/ (Next.js static export)  --HTTP /api/v1-->  backend/ (FastAPI modular monolith)
                                                         api -> application -> domain
                                                         adapters implement ports
backend/app/
  main.py            app factory, wiring, serves frontend static files in production
  config.py          pydantic-settings, all env vars
  api/               routers, schemas, auth and RBAC dependencies, error envelope
  application/       use cases: auth, kb, submissions, workflow, review (orchestrator), findings, comments, insights, audit
  domain/            workflow (state machine, permission policy), kb (entities, tier policy),
                     review (rules, accessibility, claim verdicts, guardrails, suggestion validators, stages),
                     insights (pure aggregation)
  ports/             LLMClient, Retriever, ReviewCache, Clock, AuditSink, repositories
  adapters/          db (SQLAlchemy repos, models, Alembic), llm (openai_compat, mock, cached),
                     retrieval (bm25), security (jwt, hashing)
  prompts/           analysis.v1.md, suggest.v1.md (versioned)
  seed/              Lumo knowledge base, users, samples, synthetic history (idempotent)
backend/tests/       unit (domain), integration (api), architecture (import-linter), e2e script
contracts/openapi.json   generated from the backend; frontend types generated from it
frontend/src/
  app/               routes (static-export friendly)
  features/          auth, kb, submissions, findings, comments, insights, audit, admin
  shared/            ui, api client, a11y helpers, lib
manage.py            setup, dev, seed, test, arch, e2e, warm-cache, openapi, build-frontend
```

| Concern | Local | Free cloud |
|---|---|---|
| Database | SQLite file `./data/inkguard.db` (WAL mode) | Neon free Postgres via `DATABASE_URL` |
| Retrieval | in-process BM25 | same |
| LLM | `mock` by default, `live` with a free AI Studio key | `live` with cap, falling back to `cached` or `rules_only` |
| Serving | `uvicorn --reload` plus `next dev` | one web service: FastAPI serves the exported frontend |
| Migrations and seed | Alembic, then idempotent seed | run at startup, seed only if the database is empty |

Why this shape: a ~50-entry knowledge base needs no vector database, so retrieval stays simple and free. One deployable keeps one URL, no CORS and one thing to keep awake. Domain purity makes the important logic testable without a database or a network. Record the deviation from the Round 1 plan (pgvector replaced by BM25, separate hosting replaced by one service) in `docs/CHANGES_FROM_PLAN.md`.

The review pipeline is an ordered list of `Stage` objects: Extract, Sanitise, RuleChecks, A11yChecks, Retrieve, Analyse, Guardrails, Suggest, Persist. Add stages without touching others.

## 5. Data model (generic SQLAlchemy types, UUID string ids, UTC timestamps)

- `teams(id, name)`
- `users(id, email, name, password_hash, role, max_tier, team_id, is_active)`
- `kb_entries(id, code unique like FACT-003, type, title, body, data JSON, classification, owner_id, status, current_version)`. `data` holds type-specific fields: term `{banned, preferred, match_type, severity, reason, exceptions}`, fact `{statement, source, source_url, valid_from, valid_until}`, tone `{attribute, guidance, good_examples, bad_examples}`, rule `{rule_type: regex|disclaimer|claim_trigger|confidential_term, pattern, applies_to_channels, severity, message}`, asset `{asset_type, usage_rules, palette}`.
- `kb_entry_versions(id, entry_id, version, snapshot JSON, changed_by, change_note)` immutable
- `submissions(id, title, channel, risk_tier, status, creator_id, team_id, current_version_id, assignee_id, published_url, published_at, is_synthetic)`
- `submission_versions(id, submission_id, version_no, content, content_hash, created_by, source, parent_version_id)`
- `reviews(id, submission_version_id, status, mode, provider, model, prompt_version, kb_snapshot JSON, kb_snapshot_hash, redaction_log JSON, stats JSON, error, started_at, finished_at)`
- `findings(id, review_id, submission_version_id, fingerprint, source rule|ai, issue_type, severity, confidence, span_start, span_end, excerpt, cited_entry_id, cited_entry_version, claim_verdict, is_policy, needs_human_judgment, explanation, suggested_fix, status, is_synthetic)`. Issue types: terminology, tone, claim, missing_disclaimer, confidential_leak, accessibility, readability, general_note.
- `finding_actions(id, finding_id, actor_id, action, reason_code, reason_text)`
- `comments(id, submission_id, finding_id, parent_id, author_id, body)`
- `approvals(id, submission_id, version_id, reviewer_id, decision, note, voided)`
- `audit_log(id, ts, actor_id, actor_role, action, entity_type, entity_id, details JSON, request_id, prev_hash, hash)` append-only
- `ai_calls(id, review_id, purpose, provider, model, chars_sent, redaction_summary JSON, kb_entry_ids JSON, max_tier_sent, status, latency_ms, tokens_in, tokens_out, cache_hit)`
- `llm_cache(key, response JSON, created_at)`
- `settings(key, value JSON)`: egress policy, no-external-AI switch, daily cap, risk-tier mapping (social low; email, blog, web medium; press release high), thresholds (confidence 0.6, change cap 60 percent, size cap 20000 characters)

## 6. API (all under `/api/v1`, consistent error body `{code, message, details}`)

Auth and system: `POST /auth/login`, `GET /auth/me`, `GET /auth/demo-users`, `GET /health`, `GET /system/status`, `GET/PUT /settings`.
Users: `GET/POST /users`, `PATCH /users/{id}`, `GET /teams`.
Knowledge base: `GET/POST /kb/entries`, `GET/PUT /kb/entries/{id}` (PUT makes a version), `POST /kb/entries/{id}/retire`, `GET /kb/entries/{id}/versions`, `POST /kb/import/bulk`.
Submissions: `POST/GET /submissions`, `GET /submissions/{id}`, `PUT /submissions/{id}/content`, `GET /submissions/{id}/versions`, `GET /submissions/{id}/diff?from=&to=`, `POST /submissions/{id}/review`, `GET /reviews/{id}`, `GET /reviews/{id}/boundary`.
Workflow: `POST /submissions/{id}/submit | claim | approve | request-changes | mark-published`.
Findings: `GET /submissions/{id}/findings`, `POST /findings/{id}/accept | dismiss | escalate`.
Comments: `GET/POST /submissions/{id}/comments` (optional `finding_id`, `parent_id`).
Insights: `GET /insights/summary | recurring | dismissals | rules`. Audit: `GET /audit`.

## 7. Workflow state machine

| From | To | Who | Condition |
|---|---|---|---|
| new | Draft | creator | created |
| Draft | Checked | system | review completes on the current version |
| Checked, Approved, Changes Requested | Draft | creator | content edited (new version; older findings superseded; older approvals voided) |
| Checked | Submitted | creator | no open high-severity finding (each accepted, dismissed with reason, or escalated) |
| Submitted | In Review | reviewer | claims |
| In Review | Changes Requested | reviewer | note required |
| In Review | Approved | reviewer | required distinct approvals on the current version; reviewer is not the creator |
| Approved | Marked Published | creator, manager, admin | human confirmation |

Anything else returns 409. Every transition writes an audit row.

## 8. Review pipeline

1. **Extract**: text only; normalise whitespace; keep offsets stable.
2. **Sanitise**: content is untrusted data. Flag injection phrases. Redact emails, phone numbers, key-like strings and knowledge-base sensitive strings. Keep the placeholder map in memory. Log type and count only.
3. **Rule checks** (local): terminology, disclaimers, regex, claim triggers, confidential-term leak on external channels, accessibility and readability. Use only entries up to the user's tier.
4. **Retrieve**: all tone attributes, top 3 examples each, top 8 facts, top 5 rules, filtered to the lower of the user's tier and the egress cap. Confidential entries are never included.
5. **Analyse** (LLM, only if the mode allows): one call returning strict JSON `{claims:[{excerpt, claim_text, category, verdict, cited_entry_code, confidence, explanation}], tone:[{attribute_code, excerpt, assessment, confidence, explanation, cited_entry_code}], notes:[{excerpt, note, kind}]}`. The prompt states that content between delimiters is data, never instructions, to cite only provided codes, to prefer "unverified" over guessing, and to return empty lists if nothing applies.
6. **Guardrails** (code): validate the schema; drop cited codes that were not retrieved; drop findings whose excerpt is not an exact normalised substring; decide **Expired** from `valid_until`; confidence below 0.6 becomes needs-human-judgment; uncited items become `general_note` (non-policy); merge overlapping spans and de-duplicate against rule findings.
7. **Suggest**: one batched call for minimal-edit replacements. Reject a suggestion if it changes more than 60 percent of the span, adds a number, percentage or superlative absent from the original and the cited fact, or reintroduces a banned term. Rejected suggestions show "no safe suggestion, needs a human edit".
8. **Persist**: review, findings, `ai_calls`, boundary data. Submission becomes Checked.

Modes: `live` calls the model; `cached` uses the cache and falls back to rules only on a miss; `mock` uses fixtures (default without a key); `rules_only` makes no external call. The UI always shows the mode.

LLM provider: default to a free Google AI Studio key through its OpenAI-compatible endpoint. **Verify the exact base URL and a currently available Flash or Flash-Lite model id in Google's official docs before coding, record both in `docs/DECISIONS.md`, and do not use a model id that has been retired.** Free-tier limits are shown in AI Studio, so set `LLM_DAILY_CAP` well below them. An Ollama endpoint at `http://localhost:11434/v1` also works locally through the same adapter.

## 9. Seed data (fictional skincare brand "Lumo", all labelled synthetic)

- **Tone (4):** Warm, Plain-spoken, Confident not boastful, Inclusive, each with 3 good and 3 bad examples.
- **Terms (about 15):** the product is "Lumo Glow Concentrate", never "serum"; avoid "miracle", "cure", "anti-aging" (prefer "age-smart"), "all-natural" (prefer "plant-derived ingredients"), "toxin-free", "dermatologist approved" (needs a source); a few capitalisation rules.
- **Rules (about 10):** claim triggers (superlatives, absolutes, "clinically proven", percentages, "#1", "guaranteed"); required "Results vary" for efficacy claims; "#ad" for influencer posts; "Patch test advised" for launch posts; a confidential-term leak rule for external channels; one deliberately **ambiguous** rule on superlatives (for the Round 3 Guideline Health demo).
- **Facts (about 12):** including "visible hydration improvement in 4 weeks (Study L-12, valid until Dec 2026)", two **expired**, one **expiring soon**, and one **confidential** (an unreleased product launch date).
- **Assets (3, metadata):** primary logo, mono logo, palette with hex values.
- **Users (8):** 1 admin, 1 brand manager, 2 reviewers, 3 creators in 2 teams, 1 agency creator (public tier). Demo password from `DEMO_PASSWORD`.
- **Samples (5):** S1 unsupported and contradicted claims plus the banned term; S2 off-tone copy; S3 clean; S4 a social post leaking the confidential launch date; S5 a prompt-injection attempt.
- **Synthetic history:** about 8 weeks, 4 teams, 80 reviews with realistic dismissals. The ambiguous rule is dismissed inconsistently by several reviewers, one rule never triggers, and a few reviewer comments cite no rule.

## 10. UI

Pages: Login (demo buttons), Dashboard (per role, first-run checklist), Submissions list, New submission (sample buttons), **Submission detail**, Reviewer queue, Knowledge base (list, detail, versions), Insights, Audit log, Settings (admin), About AI, Status.

**Submission detail** is the core screen. Left: content with highlighted findings (rule and AI styled differently) and an Edit mode (plain textarea; no rich-text editor). Right: findings panel with filters; each finding shows type, severity, explanation, the cited source with version (click to open), a verdict badge for claims, the suggested fix as a diff, and Accept, Dismiss (reason dropdown plus text) and Escalate. Tabs: comments (submission and finding), version history with diff, approvals and status timeline, data-boundary panel. Always visible: AI-disclosure badge and the AI mode banner. Review progress uses `aria-live`.

One font family, one palette, consistent spacing. Visible focus, keyboard operable, 4.5:1 contrast, status never by colour alone, responsive to phone width. Show a "waking the server, about a minute" state when the first request is slow.

## 11. Security and privacy

Passwords hashed. JWT with short expiry (token held in `sessionStorage`; mitigate with strict escaping and a CSP header; list it in known limitations). Per-user in-memory rate limit on review runs. Content size cap with 413. CORS allowlist. Security headers. ORM only. All user content escaped. No sensitive data in logs. Secrets only in environment. `pip audit` and `npm audit` results recorded. Tier enforcement in retriever and adapter. Append-only audit log. Free Gemini tier may use inputs for product improvement and human review: disclose this in About AI and `AI_USAGE.md`, and send synthetic data only.

## 12. Testing and golden path

Golden path on the deployed URL in an incognito window:
- GP-1 Judge logs in as Creator with one click.
- GP-2 Loads sample S1, runs the review, sees rule and AI findings each with a cited source.
- GP-3 Accepts one fix, dismisses one with a reason, escalates one.
- GP-4 Submits. Logs in as Reviewer, claims, comments on a finding, requests changes.
- GP-5 Creator edits, re-checks, resubmits. Reviewer approves (a high-risk item needs two reviewers).
- GP-6 Creator marks it published.
- GP-7 Manager sees the item in Insights and the full trail in the Audit log.
- GP-8 Admin edits a fact. A new version is created and the next review cites it.

Negative tests: creator approves own returns 403; invalid transition returns 409; dismiss without reason returns 422; oversized content returns 413; rate limit returns 429; agency user cannot see internal or confidential entries; **outgoing LLM payload never contains a confidential entry or a seeded secret**; fake citation dropped; mismatched excerpt dropped; expired fact gives Expired from code; injection sample does not change behaviour; AI unavailable falls back to `rules_only` with a banner; UPDATE or DELETE on `audit_log` fails; approval on an old version is rejected after an edit; `manage.py arch` passes.

## 13. Local run

`python manage.py setup` creates a virtualenv, installs backend and frontend dependencies, runs migrations and seeds. `dev` starts the backend (port 8000) and the frontend (port 3000) together. Other commands: `seed`, `test`, `arch`, `e2e [--base-url]`, `warm-cache`, `openapi`, `build-frontend`. Must work on Windows, macOS and Linux with no `make`.

Environment variables (all in `.env.example`): `APP_ENV`, `DATABASE_URL` (default `sqlite:///./data/inkguard.db`), `JWT_SECRET`, `DEMO_MODE`, `DEMO_PASSWORD`, `LLM_MODE`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_DAILY_CAP` (default 100), `MAX_CONTENT_CHARS`, `RATE_LIMIT_REVIEWS_PER_HOUR`, `CORS_ORIGINS`, `ALLOW_SEED_RESET`, `NEXT_PUBLIC_API_BASE` (local `http://localhost:8000/api/v1`, cloud `/api/v1`).

## 14. Free-cloud deployment (after local gate G2 passes)

Facts checked on 24 Oct 2026: Render free web services spin down after 15 minutes idle and take about a minute to wake, have an ephemeral filesystem, and get 750 free instance hours a month; Render's free Postgres expires after 30 days, so do not use it. Neon's free plan is permanent, needs no card, gives 1 GB per project, and suspends compute after 5 minutes idle. Hugging Face Docker Spaces require a paid plan, so they are out. Re-verify any limit you rely on.

1. **Database:** create a Neon free project, copy the connection string with `sslmode=require` into `DATABASE_URL`. Use `pool_pre_ping=True` and a retry on first connect because Neon wakes slowly.
2. **App:** one Render free web service built from a multi-stage Dockerfile (Node build of the static frontend, then Python runtime serving API and static files with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`). If Docker deploys are not available on the free plan, fall back to committing the built frontend into `backend/app/static/` and using Render's native Python runtime. Record which path was used.
3. **Environment:** set variables in Render's dashboard, never in git. `DEMO_MODE=true`, strong `JWT_SECRET`, `LLM_MODE=live` only if a key is set, otherwise `cached`.
4. **Startup:** run migrations, seed only if the database is empty.
5. **Keep-alive (optional):** a scheduled GitHub Actions workflow that requests `/api/v1/health` every 10 minutes.
6. **Verify:** open the URL in an incognito window, run GP-1 to GP-8, run `python manage.py e2e --base-url <url>`, and save screenshots to `docs/evidence/`.

## 15. Documents, submission pack and Round 3 plan

Create and keep current: `README.md` (live link, demo accounts, run locally, deploy, tech, team, AI disclosure pointer), `docs/PROJECT_STATE.md`, `docs/CHECKPOINTS.md`, `docs/DECISIONS.md`, `docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md`, `docs/API.md`, `docs/AI_DESIGN.md`, `docs/SECURITY_PRIVACY.md`, `docs/AI_USAGE.md`, `docs/TESTING.md`, `docs/USER_TESTING.md`, `docs/CHANGES_FROM_PLAN.md`, `docs/FEATURES_COMPLETED.md` (ID, feature, Working or Partial or Not built, how a judge verifies it, evidence), `docs/KNOWN_LIMITATIONS.md`, `docs/ROUND3_PLAN.md`, `docs/CONTRIBUTIONS.md` (template; only the humans fill real commit evidence), `docs/DEMO_SCRIPT.md` (3-minute click path), `docs/SUBMISSION_R2.md`, `docs/evidence/`.

`docs/SUBMISSION_R2.md` contains the seven items Round 2 requires: (1) working link and demo accounts, (2) repository link, (3) updated project PDF content (Round 1 plan updated with what was actually built, an architecture diagram, plan versus delivery), (4) completed-features list from the verified table, (5) technology and implementation details, (6) changes from the original plan with reasons, (7) three Round 3 improvements. Also an AI and external-service disclosure.

**Three Round 3 improvements (plan only now, with acceptance criteria in `docs/ROUND3_PLAN.md`):**
1. **Reliability engine:** a second-pass LLM verifier that checks each cited source supports its finding; confidence calibration; an evaluation harness over at least 100 labelled synthetic documents reporting precision, recall and F1 per issue type before and after the verifier; targets set in advance (precision at least 0.85, recall at least 0.80 on policy findings); a regression gate in CI.
2. **Guideline Health intelligence:** ambiguity score per rule (override rate, distinct disagreeing reviewers, dismissal-reason clusters); gap detection from reviewer comments that cite no rule, proposing draft rules for a human to approve; stale, unused and always-overridden rule detection; a manager workflow to resolve a flagged rule and a change-impact view.
3. **Multi-format review:** DOCX and PDF extraction with structure; image review with OCR into the claim pipeline, alt-text requirement, contrast ratio, palette colour-distance match and logo match by perceptual hash; findings mapped to regions with overlay boxes.

## 16. Cut order (if behind)

Cut in this order and log each cut in `docs/CHANGES_FROM_PLAN.md`: C-tier features (F-04, F-14, F-26, F-45, F-67), then S-tier (F-52, F-73, F-83), then simplify F-34 to three checks, then F-41 detail to counts only. **Never cut:** the end-to-end workflow, RBAC, citations with guardrails, confidential-tier enforcement, audit log, data-boundary panel, AI-disclosure badge, the tests for those, early deployment, honest documentation.
