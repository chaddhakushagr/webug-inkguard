# Project State: Inkguard

**Current Phase:** Gate G2 Complete / Ready for Gate G3 (Cloud Deployment)  
**Last Updated:** Sat 24 Oct 2026, 20:15 IST  
**Current Gate:** Gate G2 Complete (Target: Gate G3 - Sun 01:00 IST)  
**Lane Active:** FE (Apurrv), BE (Sparsh), AI (Kushagra)

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
- [x] Phase 2B: Findings UI, inline highlighting, interactive triage & escalation [FE]
- [x] Gate G2: Golden path GP-1..GP-6 local with full findings review & evidence screenshots [ALL]
- [ ] Gate G3: Free-cloud deployment verified, GP-1..GP-8 live incognito, insights [ALL]




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
- Phase 2B Verification (Submission Details & Interactive Findings Triage):
  - Two-Pane Responsive Layout: Wide screens feature copy content on left (7 cols) and findings panel on right (5 cols); narrow screens feature tab toggle between Copy & Details and Findings.
  - Review Execution & Live Progression: "Run Brand Review" and "Re-check Copy" buttons trigger background review pipeline with live 5-stage progression (`extracting`, `rule_checks`, `retrieving`, `analysing`, `finalising`), `aria-live` announcement, ModeChip indicator, and automatic fallback warning banner when daily cap or admin switch is active.
  - Inline Highlighting & Bidirectional Focus: `HighlightedText` renders rule checks with solid underlines and AI checks with wavy underlines; color-coded by severity (high=red, medium=amber, low=blue). Clicking highlights scrolls to and focuses corresponding finding cards in right pane and vice-versa.
  - Findings Panel & Triage Workflow:
    - Filters: Issue Type, Severity, Source (Rule vs AI), and Status (Open, Accepted, Dismissed, Escalated).
    - Summary counts: Total, Open, High Risk, Rule checks, and AI assisted.
    - Clean bill state: Renders "Clean Bill of Brand Health" when review passes with 0 findings.
    - Each Finding Card: Type tag, severity badge, `AIBadge` with confidence %, plain explanation, claim verdict badge, "Needs Human Judgment" flag, and `DiffView` showing proposed replacement.
    - "No safe suggestion" fallback state displayed when `suggested_fix` is null.
    - Accept Fix: Applies fix, increments content version, reverts status to Draft, voids prior approvals, and prompts for Re-check.
    - Dismiss Finding: `DismissDialog` enforces mandatory reason dropdown code and detailed text justification.
    - Escalate Finding: `EscalateDialog` prompts for managerial note and links escalation ticket.
    - Knowledge Base Inspector: `KBCitationDialog` opens on clicking cited entry codes (e.g. `FACT-001`, `TERM-005`), displaying full policy text and study references.
    - Inline Finding Comments: Collapsible threaded comments per finding.
  - Data Boundary Telemetry: Dedicated panel/drawer displaying characters sent, redaction breakdown (emails, phones, API keys, secrets), included entry codes, highest tier sent, and explicit mock mode zero-egress notice.
  - Role-Based Guardrails:
    - Submit for Approval is disabled with warning while any open high-severity findings exist.
    - Reviewers receive editorial view (no edit mode, comment per finding, required note for change requests, approvals progress tracker).
  - Samples S1–S5 Browser Run Verification (Mock Mode):
    - Sample S1 (`sub-sample-s1`): Spring Hydration Campaign — 32 findings flagged (contradicted cure claims, miracle superlative, FTC disclaimer missing). Submit disabled until high-severity issues resolved.
    - Sample S2 (`sub-sample-s2`): Product Teaser Email — 2 findings flagged for off-tone aggressive marketing language and missing unsubscribe requirement.
    - Sample S3 (`sub-sample-s3`): Blog Announcement — Clean, fully compliant brand announcement. Displays Clean Bill of Brand Health card.
    - Sample S4 (`sub-sample-s4`): Social Teaser — 5 findings flagged including confidential launch codename leak ("Project Aurora") on external channel.
    - Sample S5 (`sub-sample-s5`): Security Test — 3 findings flagged; prompt injection attempt ("ignore previous instructions") flagged in context while review completes safely without behavior alteration.
  - Build & Static Export: `npm run build` succeeds cleanly with all 16 static routes prerendered.
- Gate G2 Verification (Golden Path GP-1..GP-6 & Safety Audit):
  - Command output: `python manage.py test` passed 61/61 tests cleanly (7.25s).
  - Command output: `python manage.py arch` verified clean architecture (2 kept, 0 broken).
  - Golden Path Walkthrough in Mock Mode (`scripts/run_golden_path_g2.py`):
    - **GP-1**: Creator authentication (Elena Chen) -> PASS. ModeChip displays `Mock`. Dashboard loads first-run checklist. Screenshot: `docs/evidence/gp-01-login-creator.png`.
    - **GP-2**: High-risk press release created and evaluated with offline review engine -> PASS. 32 findings flagged across Rule and AI categories with explicit citations. Data boundary panel confirmed zero external egress (0 characters sent, 0 external requests). Screenshot: `docs/evidence/gp-02-sample-review.png`.
    - **GP-3**: Findings triage -> PASS. Accepted suggested fix for "miracle" (created v2 in Draft, voided prior approvals), dismissed banned term "serum" with mandatory reason code `brand_exception` and justification, escalated clinical trial claim to brand manager; cleared remaining high-severity issues. Screenshot: `docs/evidence/gp-03-triage-actions.png`.
    - **GP-4**: Creator submitted; Reviewer 1 (Marcus Vance) claimed submission (`In Review`), added threaded inline review comment, and requested changes with note (`Changes Requested`) -> PASS. Screenshot: `docs/evidence/gp-04-reviewer-changes-requested.png`.
    - **GP-5**: Creator revised content to v3 (`Draft`), re-checked in mock mode, resubmitted; Approver 1 (Marcus Vance) approved (1/2, stayed `In Review`); Approver 2 (Jordan Reed) approved (2/2 -> `Approved`); computed unified version diff v1 -> v3 -> PASS. Screenshot: `docs/evidence/gp-05-version-diff-and-approvals.png`.
    - **GP-6**: Creator marked published with live URL (`https://brand.lumo.skincare/press/spring-hydration-v3`) -> PASS (`Marked Published`). Cryptographic audit trail contains 100 SHA-256 hash-chained entries. Screenshot: `docs/evidence/gp-06-published-live.png`.
  - Negative & Safety Invariants Verified:
    - 403 on self-approval attempt by creator.
    - 409 on invalid workflow transition.
    - 422 on finding dismissal without reason code/text.
    - 413 on oversized content payload (>20,000 characters).
    - 429 on rate limit exceeded (>60 reviews/hour).
    - Agency user clearance restricted to public tier only.
    - Zero confidential entries or seeded secrets present in any outbound LLM request.
    - Code-level guardrails: hallucinated citations dropped, mismatched excerpts dropped, expired facts evaluated in code, low-confidence findings flagged for human review.
    - Prompt injection sample S5 flagged without altering evaluation behaviour.
    - Fallback to `rules_only` when daily cap is 0 or admin "no external AI" switch is enabled.
    - SQLite/Postgres audit log table immutability: UPDATE and DELETE statements raise errors.
    - Voids approvals on edit: approving an older version after a new draft is rejected with 409.
    - Backend disconnection resilience: killing backend server triggers accessible `ErrorState` component with retry button, preventing blank screen.
