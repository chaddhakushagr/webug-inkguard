# Project State: Inkguard

**Current Phase:** Phase 1 (Core Domain & Monolith Implementation)  
**Last Updated:** Sat 24 Oct 2026, 13:20 IST  
**Current Gate:** Pre-Gate 1 (Target: 17:30 IST)  
**Lane Active:** ALL (Sparsh [BE], Kushagra [AI], Apurrv [FE])

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
- [ ] Gate G1: Full Draft -> Approved -> Marked Published walkthrough & tracer deploy [ALL]

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


