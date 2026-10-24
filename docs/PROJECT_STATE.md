# Project State: Inkguard

**Current Phase:** Phase 2A Complete / Hand-off to Phase 2B (Findings UI & Interactive Triage)  
**Last Updated:** Sat 24 Oct 2026, 19:45 IST  
**Current Gate:** Gate G1 Complete (Target: Gate G2 - Sat 22:00 IST)  
**Lane Active:** BE (Sparsh) & AI (Kushagra) complete; handing off to FE (Apurrv)

## Active Milestones
- [x] Initial repository audit and folder isolation under `WeBug/`
- [x] `AGENTS.md`, `docs/SPEC.md`, and headed documentation skeletons created
- [x] Phase 0: Backend foundation, SQLAlchemy models, modular monolith structure
- [x] Phase 0: OpenAPI 3.1 specification generation (`contracts/openapi.json`) & stub routers
- [x] Phase 0: Next.js static export frontend setup, layout shell, and demo login page
- [x] Phase 0: Architecture validation (`manage.py arch`), 11 passing tests, and CLI wiring
- [x] Phase 0: Tag `p0` verified and committed
- [x] Prompt 0: UI design system, "proofreader's desk" palette, typed UI components, AppShell, login overhaul, /dev/ui component gallery, and evidence screenshots (`docs/evidence/ui-*.png`) [FE]
- [x] Prompt 1A: Backend real implementation (Auth, RBAC, KB CRUD & versioning, Submissions & diff, State machine & queue, Audit hash chaining, Seed loader) [BE]
- [x] Prompt 1B: AI domain, seed data, adapters (Lumo seed content, synthetic history, Sanitise/Rules/A11y/Guardrails/Suggest, BM25 retriever, Mock/OpenAI/Cached LLM adapters) [AI]
- [x] Prompt 1C: Core screens on the design system (KB, Submissions, Reviewer Queue, Submission Detail shell) [FE]
- [x] Gate G1: Full Draft -> Approved -> Marked Published walkthrough & tracer deploy [ALL]
- [x] Phase 2A: Review Orchestrator, findings API & persistence, action endpoints, safety tests [BE + AI]
- [ ] Phase 2B: Findings UI, inline highlighting, interactive triage & escalation [FE]
- [ ] Gate G2: Golden path GP-1..GP-6 local with full findings review & evidence screenshots [ALL]


## Completed Verification
- `manage.py setup`: Virtualenv creation, dependency installation, Alembic migration, and seeding verified.
- `manage.py test`: 54 passing tests (domain unit tests, API integration tests, architecture contract tests, table-driven state transitions).
- `manage.py arch`: 2 import-linter contracts kept (domain purity, application isolation).
- `manage.py build-frontend`: Static export compilation successful with 0 warnings (16 static routes prerendered).
- `manage.py e2e`: Live server `/api/v1/health` connectivity verified.
- Prompt 0 Verification:
  - Contrast check: All text/background pairs $\ge 4.5:1$ (WCAG 2.1 AA).
  - Component gallery: `/dev/ui` displaying all components and variants.
  - Screenshots: `docs/evidence/ui-login.png`, `docs/evidence/ui-gallery.png`, `docs/evidence/ui-dashboard.png`.
- Prompt 1A Verification:
  - JWT login with bcrypt, token expiry, 401 handling, `/auth/me`.
  - RBAC domain policy, tier clearance gating, `allowed_actions`.
  - Immutable KB versioning with snapshot history and fact validity checks.
  - Submissions lifecycle (Draft -> Checked -> Submitted -> In Review -> Approved -> Marked Published).
  - Table-driven workflow unit tests for all roles across all state transitions.
  - Self-approval blocked (403 Forbidden).
  - High-risk 2-approver requirement enforced.
  - Content edit voids approvals and resets to Draft.
  - Content diff endpoint (`difflib.unified_diff`) between arbitrary versions.
  - Threaded comments at submission and finding levels.
  - Cryptographic append-only audit trail with SHA-256 hash chaining, SQLite/Postgres immutability guards, and CSV export.
  - Idempotent seed loader (`manage.py seed`) safe to run repeatedly.
  - OpenAPI 3.1 specification regenerated (`contracts/openapi.json`).
- Prompt 1B Verification:
  - Seed content for fictional brand "Lumo" (4 tone attributes, 15 terms with match types/exceptions, 10 rules, 12 facts with 2 expired / 1 expiring soon / 1 confidential, 3 assets, 8 users, 5 benchmark submissions S1-S5, 80-review synthetic history).
  - Pure Python review pipeline in `app.domain.review` with zero external/database dependencies: `ExtractStage`, `SanitiseStage` (injection phrase flags, secret redaction), `RuleChecksStage` (regex, terminology, disclaimers, leaks), `A11yChecksStage` (Flesch-Kincaid grade, long sentences, caps runs, empty alt text, heading skips), `GuardrailsStage` (dropping hallucinations, code-based expired fact verdict, confidence calibration), and `SuggestionValidatorStage` (60% change cap, zero ungrounded superlatives/percentages).
  - In-process BM25 lexical retriever with tier filtering and confidential entry egress boundary.
  - LLM port with Mock (deterministic fixtures), OpenAI-compatible (httpx with exponential backoff and security assertions), and Cached adapters.
  - Versioned prompts in `backend/app/prompts/` (`analysis.v1.md`, `suggest.v1.md`).
  - 10 offline unit tests in `backend/tests/unit/test_ai_domain.py`.
- Prompt 1C Verification:
  - Frontend static export: `npm run build` generates 16 routes (`/`, `/about-ai`, `/audit`, `/dashboard`, `/dev/ui`, `/insights`, `/kb`, `/queue`, `/reviewer-queue`, `/settings`, `/submission`, `/submissions`, `/submissions/new`) with 0 errors.
  - Auth: demo persona login cards, manual credentials form, `sessionStorage` token persistence, global 401 interception with re-login dialog, and role clearance guard (`AuthGuard`).
  - Role-specific Dashboards: Creator (my drafts, items needing action, 4-step checklist with progress and S1/S2/S4 sample buttons), Reviewer (queue size, claimed items), Manager & Admin (status counts, expiring facts alert, insights and audit links).
  - Knowledge Base: type, tier, status, and expiring filters; type-specific field views (terms, facts, rules, tone, assets); version history with inline `DiffView`; immutable edit form.
  - Submissions & Detail Shell: filterable list, new submission form with S1 to S5 one-click loaders and auto risk-tier calculation; detail shell with `StatusStepper`, context-sensitive primary actions based on `allowed_actions`, plain textarea Edit mode, Versions tab with `DiffView`, Comments tab (threaded submission-level), Approvals timeline, and Findings panel placeholder.
  - Reviewer Queue: unassigned vs claimed views, filter by risk tier and submission age, and one-click "Claim" action transitioning items to In Review.
  - Evidence screenshots: captured into `docs/evidence/fe-*.png`.
- Gate G1 Verification:
  - Command output: `python manage.py test` passed 54/54 tests cleanly.
  - Command output: `python manage.py arch` verified clean architecture (2 kept, 0 broken).
  - Live End-to-End Walkthrough: Executed multi-role lifecycle via real backend on port 8000:
    1. Creator created high-risk submission (`channel=press_release`, `risk_tier=high`, Version 1, `Draft`).
    2. Creator edited content -> Version 2, reverted to `Draft`.
    3. Review triggered in offline mock mode -> transitioned to `Checked`.
    4. Creator submitted -> transitioned to `Submitted`.
    5. Reviewer 1 claimed -> transitioned to `In Review`.
    6. Reviewer 1 commented -> threaded comment recorded.
    7. Reviewer 1 requested changes -> transitioned to `Changes Requested`.
    8. Creator revised content -> Version 3, resubmitted -> `Checked` -> `Submitted`.
    9. Multi-reviewer check: Reviewer 1 approved (1/2, remained `In Review`), Reviewer 2 approved (2/2 -> transitioned to `Approved`).
    10. Creator marked published -> transitioned to `Marked Published` with live URL.
    11. Admin edited fact `FACT-001` -> Version 2 appeared with full snapshot history.
    12. Agency creator access restricted strictly to `public` tier entries; internal and confidential entries masked.
    13. Self-approval blocked: Creator attempting to approve own submission refused with `403 Forbidden`.
    14. Cryptographic audit log: 11 hash-chained rows verified with SHA-256 integrity intact.
  - Evidence screenshots: captured into `docs/evidence/g1-*.png`.
- Phase 2A Verification:
  - Command output: `python manage.py test` passed 59/59 tests (added 5 safety and end-to-end review engine tests).
  - Command output: `python manage.py arch` verified clean architecture (2 kept, 0 broken).
  - Background Review Pipeline: `ReviewOrchestrator` runs asynchronously in background tasks, persisting stage progression (`extracting`, `rule_checks`, `retrieving`, `analysing`, `finalising`, `completed`), returning review ID immediately, and setting submission to `Checked` on completion.
  - Modes & Offline Mock: Default `mock` mode executes 100% offline with zero keys and zero network.
  - Safety & Boundary:
    - Egress policy strictly asserts zero confidential entries or seeded secrets are transmitted.
    - Daily cap on live LLM calls stored in settings, with automatic fallback to `rules_only` and reasons logged on review record.
    - Admin "no external AI" switch honored: zero outbound calls with fallback.
    - `GET /reviews/{id}/boundary` returns comprehensive telemetry; explicitly confirms offline zero-egress in mock mode.
  - Findings Triage Endpoints:
    - `GET /submissions/{id}/findings` returns context-sensitive `allowed_actions`.
    - `POST /findings/{id}/accept` applies replacement as a new content version, voids prior approvals, resets workflow to Draft, supersedes older findings, and raises 409 Conflict if text span changed.
    - `POST /findings/{id}/dismiss` strictly enforces non-empty `reason_code` and `reason_text` (422 Unprocessable Entity otherwise).
    - `POST /findings/{id}/escalate` records `FindingAction`, logs audit row, and posts escalation comment.
    - Voids approvals on edit: approving an older version after a new draft is rejected (409 Conflict).
  - OpenAPI 3.1 specification regenerated (`contracts/openapi.json`) with zero duplicate operation IDs or warnings.
  - Sample S1 verified through API in mock mode, generating full Review, Findings (31 findings), and Boundary JSON.



