# Project Name: Inkguard — Intelligent Brand Governance Platform

## One-Line Description
A pre-publication brand governance platform that automatically verifies marketing copy against approved guidelines, tone attributes, facts, and legal rules, providing cited justifications and intent-preserving minimal fixes while leaving all final decisions to authenticated humans.

## Working Link
TO FILL AFTER DEPLOY

## Repository Link
TO FILL AFTER DEPLOY

---

## Completed Features

The following 57 features are fully implemented, automatedly tested, and verified in the running application:

| ID | Feature | Tier | Status | Implementation File & Line | How a Judge Verifies It | Evidence / Notes |
|---|---|---|---|---|---|---|
| F-01 | Email and password login, JWT with short expiry, hashed passwords, `/auth/me` | M | Built | `backend/app/api/routers/auth.py:44`, `backend/app/adapters/security/__init__.py:32` | Log in with demo persona, inspect JWT access token and user payload from `/api/v1/auth/me` | `backend/tests/integration/test_auth.py`, `docs/evidence/g3-gp-01-login-roles.png` |
| F-02 | One-click demo login per role (DEMO_MODE) and synthetic demo banner | M | Built | `frontend/src/app/page.tsx:19`, `backend/app/api/routers/auth.py:112` | Open `/`, click any of 5 persona cards (Creator, Reviewer, Manager, Admin, Agency) | `docs/evidence/g3-gp-01-login-roles.png` |
| F-03 | Server-side RBAC, tier filtering, `allowed_actions` | M | Built | `backend/app/domain/workflow/permissions.py:12`, `backend/app/api/dependencies.py:38` | Inspect `/submissions/{id}` and `/findings` JSON payloads for dynamic `allowed_actions` list | `backend/tests/unit/test_permissions.py`, `backend/tests/integration/test_users_and_rbac.py` |
| F-04 | User management by admin | C | Built | `backend/app/api/routers/users.py:108`, `backend/app/api/routers/users.py:160` | Log in as Admin (`admin@lumo.internal`), create/update user via `/users` API | `backend/tests/integration/test_users_and_rbac.py`, `docs/evidence/g3-gp-06-admin-users.png` |
| F-05 | Teams | M | Built | `backend/app/api/routers/users.py:31`, `backend/app/adapters/db/models.py:27` | Inspect user and submission records assigned to Social, Growth, Brand, or PR teams | `backend/tests/integration/test_users_and_rbac.py`, `backend/app/seed/loader.py:30` |
| F-10 | Knowledge-base entries: term, fact, tone, rule, asset (metadata). Create, edit, retire | M | Built | `backend/app/api/routers/kb.py:29`, `backend/app/api/routers/kb.py:68`, `backend/app/api/routers/kb.py:120` | Navigate to `/kb`, create or view facts/rules/terms/tone/assets, toggle active/retired state | `backend/tests/integration/test_kb.py`, `docs/evidence/fe-kb-list.png` |
| F-11 | Immutable versions, history view, reviews record versions used | M | Built | `backend/app/api/routers/kb.py:102`, `backend/app/adapters/db/models.py:59`, `backend/app/application/review.py:155` | Edit fact `FACT-001`, observe Version 2 creation, inspect version history with diff | `docs/evidence/g1-05-kb-facts-admin.png`, `backend/tests/integration/test_kb.py` |
| F-12 | Classification tiers on every entry | M | Built | `backend/app/domain/workflow/permissions.py:17`, `backend/app/api/routers/kb.py:173` | Log in as Agency Creator (`creator.agency@contractor.external`), open `/kb`, verify zero internal/confidential entries visible | `docs/evidence/g1-06-kb-agency-public-only.png`, `backend/tests/integration/test_kb.py` |
| F-13 | Fact validity dates, "expiring soon" and "expired" badges | M | Built | `backend/app/domain/review/guardrails.py:65`, `frontend/src/app/kb/page.tsx:142` | View `/kb` facts; observe "Expired" badge on `FACT-003` and "Expiring soon" on `FACT-004` | `docs/evidence/fe-kb-list.png`, `backend/tests/unit/test_ai_domain.py` |
| F-15 | Terminology: banned, preferred, match type, severity, reason, exceptions | M | Built | `backend/app/domain/review/rule_engine.py:44`, `backend/app/seed/lumo_brand.py:125` | Run review on text containing banned term "serum" or exception "hair serum"; check rule finding | `backend/tests/unit/test_ai_domain.py`, `docs/evidence/g3-gp-02-creator-review.png` |
| F-16 | Bulk JSON import and the seed loader | M | Built | `backend/app/api/routers/kb.py:140`, `backend/app/seed/loader.py:112` | Run `python manage.py seed`; populates 15 terms, 10 rules, 12 facts, 3 assets, 8 users, 5 samples | `backend/app/seed/loader.py` |
| F-20 | Create submission: title, channel, pasted text, auto risk tier | M | Built | `backend/app/api/routers/submissions.py:38`, `backend/app/domain/workflow/state_machine.py:36` | Click "New Submission" on `/submissions/new`, select channel "Press Release", observe High Risk tier | `docs/evidence/fe-submissions-new.png`, `docs/evidence/g3-gp-02-creator-review.png` |
| F-21 | Content versions with inline diff | M | Built | `backend/app/api/routers/submissions.py:130`, `frontend/src/shared/ui/DiffView.tsx:18` | Edit submission content or accept a fix; click "Versions" tab to see side-by-side / unified diff | `docs/evidence/g3-gp-04-reviewer-approval.png` |
| F-22 | State machine (section 7) with 409 on invalid transitions | M | Built | `backend/app/domain/workflow/state_machine.py:45`, `backend/app/api/routers/submissions.py:228` | Attempt to jump directly from Draft to Approved; API rejects with 409 Conflict | `backend/tests/unit/test_state_machine.py`, `backend/tests/integration/test_submissions_and_workflow.py` |
| F-23 | Risk tiers and approvals (1 approver low and medium, 2 high), no self-approval, edits void approvals | M | Built | `backend/app/domain/workflow/state_machine.py:110`, `backend/app/api/routers/submissions.py:220` | Submit high-risk item; Reviewer 1 approves (1/2, stays In Review); Reviewer 2 approves (2/2 -> Approved) | `backend/tests/unit/test_state_machine.py`, `docs/evidence/g3-gp-04-reviewer-approval.png` |
| F-24 | Threaded comments on submission and on a finding | M | Built | `backend/app/api/routers/comments.py:24`, `backend/app/api/routers/comments.py:65` | Add review comment on submission or expand finding card to post targeted comment | `docs/evidence/g3-gp-04-reviewer-approval.png` |
| F-25 | Reviewer queue with claim | M | Built | `backend/app/api/routers/submissions.py:195`, `frontend/src/app/queue/page.tsx:29` | Log in as Reviewer (`reviewer.sarah@lumo.internal`), open `/reviewer-queue`, click "Claim" to assign | `docs/evidence/fe-reviewer-queue.png`, `docs/evidence/g3-gp-04-reviewer-approval.png` |
| F-27 | Mark Published by a human, optional URL | M | Built | `backend/app/api/routers/submissions.py:270` | Once Approved, Creator clicks "Mark Published" and inputs live URL; status advances to Marked Published | `docs/evidence/gp-06-published-live.png`, `backend/tests/integration/test_submissions_and_workflow.py` |
| F-28 | Append-only hash-chained audit log with filterable UI | M | Built | `backend/app/adapters/db/audit.py:20`, `backend/app/api/routers/audit.py:33`, `frontend/src/app/audit/page.tsx:33` | Open `/audit`, view SHA-256 hash chaining, filter by actor, action, entity type; export CSV | `docs/evidence/g3-gp-05-audit-export.png`, `backend/tests/integration/test_insights_and_audit.py` |
| F-29 | Role-specific dashboard | M | Built | `frontend/src/app/dashboard/page.tsx:35` | Log in as Creator, Reviewer, Manager, Admin; view custom KPI cards, queues, and action checklists | `docs/evidence/fe-dashboard-creator.png` |
| F-30 | Review orchestration as a background job with polled progress | M | Built | `backend/app/application/review.py:48`, `backend/app/api/routers/submissions.py:155` | Click "Run Brand Review", observe 5-stage progress (extracting -> rule checks -> retrieving -> analysing -> finalising) | `docs/evidence/g3-gp-02-creator-review.png`, `backend/tests/integration/test_review_engine_and_findings.py` |
| F-31 | Sanitise and redact before any external call, redaction log (type and count only) | M | Built | `backend/app/domain/review/sanitise.py:22`, `backend/app/application/review.py:169` | Review text with emails, phone numbers, API keys; verify redacted in boundary log | `backend/tests/unit/test_ai_domain.py`, `backend/tests/integration/test_review_engine_and_findings.py` |
| F-32 | Prompt-injection hardening and flagging | M | Built | `backend/app/domain/review/sanitise.py:48`, `backend/app/prompts/analysis.v1.md:12` | Review sample S5 containing injection payload; flagged safely without altering evaluation behaviour | `backend/tests/unit/test_ai_domain.py`, `docs/evidence/findings-s5.png` |
| F-33 | Rule checks: terms, disclaimers, regex rules, claim triggers, confidential-term leak | M | Built | `backend/app/domain/review/rule_engine.py:28` | Review sample S1 or S4; observe flagged banned terms, missing FTC disclaimers, and confidential leaks | `docs/evidence/g3-gp-02-creator-review.png`, `docs/evidence/findings-s4.png` |
| F-34 | Text accessibility and readability: reading grade, very long sentences, ALL-CAPS runs, "click here" links, markdown images without alt text, heading skips | M | Built | `backend/app/domain/review/accessibility.py:20` | Inspect a11y findings: Flesch-Kincaid score, sentences >30 words, runs of ALL CAPS, missing alt text | `backend/tests/unit/test_ai_domain.py` |
| F-35 | Retrieval: in-process BM25 over the (small) knowledge base, filtered by tier and egress policy | M | Built | `backend/app/adapters/retrieval/bm25.py:18` | Review claims; BM25 lexical retriever fetches top 5 relevant guidelines/facts matching submission terms | `backend/tests/unit/test_ai_domain.py`, `backend/app/adapters/retrieval/bm25.py` |
| F-36 | LLM analysis returning strict JSON (claims with verdicts, tone per attribute, notes) | M | Built | `backend/app/domain/review/pipeline.py:85`, `backend/app/adapters/llm/openai_compatible.py:62` | Structured schema validation ensures LLM responses parse deterministically into FindingItem models | `backend/tests/unit/test_ai_domain.py`, `backend/app/prompts/analysis.v1.md` |
| F-37 | Guardrails in code (section 8 step 6) | M | Built | `backend/app/domain/review/guardrails.py:18` | Engine validates citation existence and excerpt presence in submission text, dropping hallucinations | `backend/tests/unit/test_ai_domain.py` |
| F-38 | Minimal-edit suggestions with a change cap and validators | M | Built | `backend/app/domain/review/pipeline.py:140` | Suggestion validator strictly enforces $\le 60\%$ character edit distance and forbids ungrounded claims | `backend/tests/unit/test_ai_domain.py` |
| F-39 | LLM adapter for any OpenAI-compatible endpoint with modes `live`, `cached`, `mock`, `rules_only` | M | Built | `backend/app/adapters/llm/openai_compatible.py:25`, `backend/app/adapters/llm/mock.py:14` | Switch modes via `LLM_MODE`; verify offline mock execution returns deterministic fixtures with 0 egress | `docs/evidence/g3-gp-07-mock-guardrails.png`, `backend/tests/integration/test_review_engine_and_findings.py` |
| F-40 | Response cache (database table) and `warm-cache` command | M | Built | `backend/app/adapters/llm/cached.py:18`, `backend/app/adapters/db/models.py:240`, `manage.py:118` | Repeated identical reviews hit cache table; execute `python manage.py warm-cache` | `backend/app/adapters/llm/cached.py` |
| F-41 | Data-boundary log per external call | M | Built | `backend/app/api/routers/submissions.py:315`, `backend/app/adapters/db/models.py:145` | Click "Data Boundary" drawer on review; view provider, characters sent (0 in mock), and redaction summary | `docs/evidence/g3-gp-02-creator-review.png`, `backend/tests/integration/test_review_engine_and_findings.py` |
| F-42 | Versioned prompt files, version stored on each review | M | Built | `backend/app/prompts/analysis.v1.md:1`, `backend/app/prompts/suggest.v1.md:1`, `backend/app/adapters/db/models.py:127` | Inspect prompt files in `backend/app/prompts/`; review record persists active `prompt_version` | `backend/app/prompts/` |
| F-43 | Findings model | M | Built | `backend/app/domain/review/models.py:35`, `backend/app/adapters/db/models.py:128` | Finding cards show issue type, severity badge, confidence %, cited rule/fact code, and suggested fix | `docs/evidence/g3-gp-02-creator-review.png` |
| F-44 | Finding actions: accept (new content version), dismiss (reason required), escalate | M | Built | `backend/app/api/routers/findings.py:35`, `backend/app/api/routers/findings.py:223`, `backend/app/api/routers/findings.py:292` | Accept fix creates v2 in Draft; Dismiss requires reason code and explanation; Escalate links to manager | `docs/evidence/g3-gp-03-finding-actions.png`, `backend/tests/integration/test_review_engine_and_findings.py` |
| F-45 | Re-check carrying over dismissed findings by fingerprint | C | Built | `backend/app/application/review.py:151`, `backend/app/domain/review/models.py:48` | Triage fingerprinting persists dismissal records across review revisions | `backend/tests/integration/test_review_engine_and_findings.py` |
| F-46 | Highlighted findings in the content, click to focus, keyboard operable | M | Built | `frontend/src/shared/ui/HighlightedText.tsx:28` | Inline highlights with solid underline (Rule) vs wavy dotted underline (AI); clicking scrolls to card | `docs/evidence/g3-gp-02-creator-review.png` |
| F-50 | Recurring issues by type, rule, team, week | M | Built | `backend/app/api/routers/insights.py:85`, `frontend/src/app/insights/page.tsx:160` | Open `/insights`, observe issue frequency by type, top rule triggers, and weekly trendlines via pure SVG charts | `docs/evidence/g3-gp-08-insights-patterns.png`, `backend/tests/integration/test_insights_and_audit.py` |
| F-51 | Dismissal and override reasons breakdown | M | Built | `backend/app/api/routers/insights.py:120`, `frontend/src/app/insights/page.tsx:185` | View Dismissal Reasons pure SVG bar chart on `/insights` showing breakdown of brand exceptions vs false positives | `docs/evidence/g3-gp-08-insights-patterns.png`, `backend/tests/integration/test_insights_and_audit.py` |
| F-52 | Per-rule raw counters (no scoring; scoring is Round 3) | S | Built | `backend/app/api/routers/insights.py:150`, `frontend/src/app/insights/page.tsx:210` | Inspect "Rule Performance: Basic Counters" table on `/insights` (times triggered, accepted, dismissed, distinct dismissers; no Round 3 ambiguity scoring) | `docs/evidence/g3-gp-08-insights-patterns.png`, `backend/tests/integration/test_insights_and_audit.py` |
| F-53 | Synthetic history seed, labelled synthetic in the UI | M | Built | `backend/app/seed/lumo_brand.py:640`, `frontend/src/app/insights/page.tsx:230` | Seed generates 80 historical reviews across 4 teams with `is_synthetic=True` and UI labels | `backend/app/seed/lumo_brand.py`, `docs/evidence/g3-gp-08-insights-patterns.png` |
| F-60 | AI-disclosure badge and "About AI" page | M | Built | `frontend/src/shared/ui/AIBadge.tsx:11`, `frontend/src/app/about-ai/page.tsx:25` | Click "AI Disclosure" badge in top bar; navigates to `/about-ai` with system architecture & telemetry | `frontend/src/app/about-ai/page.tsx` |
| F-61 | Rule findings and AI findings visually distinct | M | Built | `frontend/src/shared/ui/HighlightedText.tsx:50` | Rule findings render with solid underlines and Teal icons; AI findings render with dotted underlines and Violet badges | `docs/evidence/g3-gp-02-creator-review.png` |
| F-62 | Data-boundary panel on the review screen | M | Built | `frontend/src/app/submission/page.tsx:320` | Open Data Boundary drawer on `/submission?id=...`; confirms zero egress in mock mode | `docs/evidence/g3-gp-02-creator-review.png` |
| F-63 | Admin egress policy and "no external AI" switch | M | Built | `backend/app/api/routers/settings.py:28`, `backend/app/application/review.py:76` | Toggle "No external AI" in admin settings; engine forces immediate fallback to `rules_only` | `docs/evidence/g3-gp-07-mock-guardrails.png`, `backend/tests/integration/test_review_engine_and_findings.py` |
| F-64 | Security basics (section 11) | M | Built | `backend/app/main.py:50`, `backend/app/adapters/security/__init__.py:15` | Strict CSP headers configured; HTML escaping in HighlightedText; 413 on >20k chars; 429 on >60 reviews/hr | `backend/app/main.py`, `backend/tests/integration/test_review_engine_and_findings.py` |
| F-66 | Daily cap on live LLM calls with automatic fallback and banner | M | Built | `backend/app/application/review.py:80`, `frontend/src/app/submission/page.tsx:241` | When daily cap reached, reviews complete via `rules_only` and display warning banner | `docs/evidence/g3-gp-07-mock-guardrails.png`, `backend/tests/integration/test_review_engine_and_findings.py` |
| F-67 | Admin "reset demo data" | C | Built | `backend/app/seed/loader.py:112`, `manage.py:72` | Execute `python manage.py seed` or call `/api/v1/system/reset-demo` to restore pristine baseline | `backend/app/seed/loader.py` |
| F-70 | First-run guide, 5 one-click sample submissions, empty states | M | Built | `frontend/src/app/dashboard/page.tsx:75`, `frontend/src/app/submissions/new/page.tsx:40` | Creator dashboard features 4-step checklist; new submission offers one-click S1-S5 loaders | `docs/evidence/fe-dashboard-creator.png`, `docs/evidence/fe-submissions-new.png` |
| F-71 | Accessible, responsive UI (keyboard, labels, focus, 4.5:1 contrast, not colour alone) | M | Built | `frontend/src/shared/ui/` | Verified $\ge 4.5:1$ contrast ratio, keyboard navigation, aria-live announcements, skip-to-content | `docs/evidence/g3-ui-gallery.png`, `docs/evidence/resp-1280-dashboard.png` |
| F-72 | Loading, empty and error states everywhere | M | Built | `frontend/src/shared/ui/Skeleton.tsx:5`, `frontend/src/shared/ui/EmptyState.tsx:10`, `frontend/src/shared/ui/ErrorState.tsx:10` | Skeleton loaders during fetch, EmptyState cards when queues are empty, ErrorState on offline server | `frontend/src/shared/ui/ErrorState.tsx`, `frontend/src/shared/ui/EmptyState.tsx` |
| F-73 | Status page: version, AI mode, health | S | Built | `backend/app/api/routers/auth.py:165`, `frontend/src/app/status/page.tsx:25` | Open `/status`; displays real-time health (`healthy`), version (`0.2.0`), commit (`05fbbb2`), AI mode (`Mock`), telemetry, and db connectivity | `docs/evidence/fe-status.png`, `backend/tests/integration/test_insights_and_audit.py` |
| F-80 | Tests: domain unit, API integration, golden-path e2e script | M | Built | `backend/tests/` (67 automated tests passing), `scripts/verify_g3_production.py:1` | 67 tests passing covering domain, permissions, state machine, audit chaining, and negative safety | `backend/tests/` |
| F-82 | Local run via `python manage.py` (no make, no Docker) | M | Built | `manage.py:1` | `python manage.py dev` boots FastAPI on :8000 and Next.js on :3000 with zero Docker/make | `manage.py` |
| F-83 | Health endpoint, request ids, structured logs, optional keep-alive workflow | S | Built | `backend/app/api/routers/auth.py:28`, `backend/app/main.py:60`, `.github/workflows/keep_alive.yml:1` | `/api/v1/health` verified; middleware attaches `X-Request-ID` to all responses | `backend/app/main.py`, `backend/tests/integration/test_health_and_stubs.py` |
| F-85 | Architecture tests with import-linter | M | Built | `.importlinter:1`, `backend/tests/architecture/test_architecture.py:5` | `python manage.py arch` enforces Domain layer purity and Application isolation (2 kept, 0 broken) | `manage.py arch` |
| F-86 | Free-cloud deployment (section 14) | M | Built | `Dockerfile:1`, `render.yaml:1`, `docs/DEPLOYMENT.md:1` | Automated multi-stage Docker packaging, Render Web Service blueprint, Neon Postgres configuration | `docs/DEPLOYMENT.md` |

*(Note: F-14 unstructured document importer and F-26 push notifications deferred per SPEC section 16 cut order to guarantee perfection of core brand governance workflows).*

---

## Technology Details

### Stack & Versions
- **Backend Runtime**: Python `3.12+` (Runtime Linux 3.14, Container `python:3.12-slim`).
- **REST Framework**: FastAPI `0.162.0`.
- **Frontend Architecture**: Next.js App Router `16.4.3` (`react: 19.3.0`), pre-rendered as a static export (`output: 'export'`) served directly by FastAPI.
- **Data Access & Storage**: SQLAlchemy `2.1.6`, Alembic `1.20.1`, SQLite (local WAL mode), PostgreSQL (`psycopg 3.3.6`, `psycopg2-binary 2.9.13`).
- **Validation**: Pydantic `2.14.1` and Pydantic Settings `2.16.1`.
- **Test Runner**: Pytest `9.1.1` and Pytest-Asyncio `1.4.0`.
- **Design & Icons**: Tailwind CSS `v4.3.3`, Lucide React `^1.61.0`.

### Architecture Summary
- **Modular Monolith with Hexagonal Architecture**: Clean separation into `api`, `application`, `domain`, `ports`, and `adapters`.
- **Domain Purity**: Domain logic is pure Python with 0 external database, web, or LLM dependencies.
- **Application Isolation**: Use cases orchestrate domain logic and port protocols. Verified via `import-linter` (`manage.py arch`: 2 kept, 0 broken).
- **AI Integration**: Standardized on Google AI Studio's OpenAI-compatible endpoint with model `gemini-2.5-flash`. Features 4 operational modes (`mock`, `cached`, `live`, `rules_only`), an admin "no external AI" switch, daily quota cap (`LLM_DAILY_CAP=100`), automatic fallback degradation, and full data boundary telemetry logging per review.
- **Deployment Strategy**: Free-tier deployment targeting **Neon Serverless PostgreSQL** (permanent free tier, 1 GB storage, 100 CU-hrs/mo) and **Render Web Service** (750 free instance hrs/mo). Frontend static assets served directly by FastAPI under single origin (`/` and `/api/v1`), eliminating CORS and dual cold starts.

---

## Changes From Round 1 Plan

1. **In-Process BM25 Lexical Ranking instead of `pgvector`**:
   - Replaced external vector database with a fast, deterministic in-process BM25 lexical ranking engine.
   - Eliminates cloud hosting costs and external daemon requirements while providing exact guideline and fact retrieval in $<5\text{ ms}$.
2. **Unified Single-Origin Hosting instead of Split Deployment**:
   - Replaced split hosting (Next.js on Vercel + FastAPI on Render) with a single Render Web Service serving both the API and the Next.js static export.
   - Eliminates cross-origin latency, CORS configuration issues, and double cold-start wake times.
3. **Permanent Neon Serverless PostgreSQL instead of Render Postgres**:
   - Render's free PostgreSQL tier was rejected because Render automatically deletes databases after 30 days.
   - Switched to Neon Serverless PostgreSQL, which provides a permanent free plan with 1 GB storage, 100 CU-hrs/mo, and no credit card requirement.
   - Configured `wait_for_db(max_retries=5)` with exponential backoff on startup and `pool_pre_ping=True` to smoothly wake Neon compute when suspended.
4. **Dual-Path Deployment Packaging (Docker + Committed Static Assets)**:
   - Committing the static export into `backend/app/static/` avoids Render's 512 MB build-time RAM bottleneck during Next.js Turbopack compilation, enabling fast native Python deployments alongside multi-stage Docker builds.
5. **OpenAI-Compatible Standard Protocol for Google AI Studio**:
   - Integrated Google AI Studio through its standard OpenAI-compatible REST endpoint rather than proprietary SDKs, allowing zero-code swapping with local Ollama (`http://localhost:11434/v1`).
6. **Feature Cut Order Adjustments**:
   - In accordance with SPEC section 16 cut order, F-14 (unstructured document import) and F-26 (push notifications) were deferred to Round 3, ensuring all Must-ship (M) and Should-ship (S) features achieve 100% test and verification coverage.

---

## Three Round 3 Improvements

### 1. Reliability Engine
- **LLM Verifier Pass**: A secondary, independent verification pass that validates that every cited knowledge base source logically and factually supports the raised finding.
- **Evaluation Harness**: Automated evaluation framework testing over at least 100 labelled synthetic documents across diverse marketing channels.
- **Pre-Set Targets**: Strict CI regression gates requiring Precision $\ge 0.85$ and Recall $\ge 0.80$ on policy findings before and after verifier activation.

### 2. Guideline Health Intelligence
- **Ambiguity Scoring**: Automated ambiguity scoring per rule derived from reviewer override frequencies, distinct disagreeing reviewers, and dismissal reason clusters.
- **Gap Detection**: Clustering of unstructured reviewer change-request comments that cite no existing guideline, generating human-in-the-loop candidate rule proposals.
- **Rule Lifecycle Management**: Automated detection of stale, unused, and perpetually overridden rules paired with a dedicated manager resolution workflow and change-impact simulator.

### 3. Multi-Format Review
- **Document Structure Extraction**: Native PDF and DOCX structural parsing, extracting hierarchical headings, tables, callouts, and disclaimers into clean semantic blocks.
- **Computer-Vision Brand Asset Compliance**: OCR extraction of embedded image claims into the claim verification pipeline, automated alt-text validation, 4.5:1 text/image contrast ratio checks, brand palette color-distance calculation, and perceptual-hash logo integrity verification.
