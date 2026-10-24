# Checkpoints & Gates Log

## Gate Schedule & Status

| Gate | Target Time (IST) | Status | Commit / Tag | Summary & Evidence |
|---|---|---|---|---|
| **Phase 0 (Exit)** | Sat 13:45 | **DONE** | `p0` | Monolith scaffold, contracts/openapi.json, 15 models, stubs, 11 tests, Next.js static export |
| **Prompt 0 (UI)** | Sat 14:15 | **DONE** | `839cece` | Proofreader design system, typed UI components, AppShell, login overhaul, gallery, evidence screenshots |
| **Prompt 1A (BE)** | Sat 14:50 | **DONE** | `0dfb8b3` | Real JWT auth, RBAC domain, immutable KB versioning, Submissions & diff, Table-driven workflow, Hash-chained audit, Seed loader |
| **Prompt 1B (AI)** | Sat 15:15 | **DONE** | `fabf445` | AI review pipeline, BM25 retriever, LLM adapters, Lumo seed content, synthetic history, 10 offline tests |
| **Prompt 1C (FE)** | Sat 15:45 | **DONE** | `2aac793` | Core screens on design system, role dashboards, KB diff, submissions shell, reviewer queue, static export |
| **G1** | Sat 19:30 | **DONE** | `g1` | Full workflow verified: Draft -> Approved -> Marked Published, 2-reviewer requirement, fact v2, agency isolation, self-approval refusal, SHA-256 audit chaining |
| **G2** | Sat 22:00 | **DONE** | `g2` | Golden path GP-1..GP-6 executed in mock mode with real running app; 61 tests passing (including all SPEC sec 12 safety & negative tests); 2 arch contracts kept; evidence screenshots in docs/evidence/gp-*.png |
| **G3** | Sun 01:00 | **DONE** | `g3` | Free-cloud deployment readiness verified; GP-1..GP-8 executed on local production run (PostgreSQL + FastAPI + static Next.js export); Cold-start UX verified; zero secrets; /dev/ui reachable; evidence screenshots in docs/evidence/g3-*.png |
| **G5** | Sun 07:30 | Planned | `v0.2.0-round2` | Hardening, audit logs, doc pack complete, ready for submission |

### Phase 0 Verification Notes
- CLI: `python manage.py setup`, `test`, `arch`, `openapi`, `build-frontend`, and `e2e` verified.
- Backend: Modular monolith structure created; 15 SQLAlchemy models with Alembic initial migration.
- Clean Architecture: `import-linter` contracts enforced via `manage.py arch`.
- Frontend: Next.js 16 static export built cleanly with TypeScript and Tailwind CSS; typed API client configured.
- Invariants: Creator cannot approve own submission enforced in domain tests.

### Prompt 0 (UI Design System & App Shell) Notes
- Design Tokens: Light theme "Proofreader's desk" palette (Ink Navy #1F2A44, Teal #0F766E, Paper #F7F7F4, Surface #FFFFFF, Border #E2E5EA, Muted #5B6475; High #B42318, Medium #B45309, Low #175CD3, Success #067647).
- WCAG AA: Contrast ratios verified $\ge 4.5:1$ across all text/background pairs.
- Typed Components: Button, Input, Textarea, Select, Badge, Card, Tabs, Dialog, Toast, Tooltip, Table, EmptyState, ErrorState, Skeleton, Banner, StatusStepper, DiffView, HighlightedText (solid for Rule vs wavy dotted for AI), PageHeader, AIBadge, ModeChip.
- AppShell: Sidebar (collapses under 1024px), top bar with ModeChip and demo role switcher, skip-to-content, teal focus rings.
- Login Redesign: 2-column layout with 5 demo-user cards and manual fallback.
- Component Gallery: `/dev/ui` showing all component variants.
- Static export: `npm run build` succeeds cleanly. Evidence screenshots saved in `docs/evidence/ui-*.png`.

### Gate G2 Verification Notes
- Executed Golden Path GP-1 through GP-6 on live running services with full evidence captures (`docs/evidence/gp-*.png`):
  - **GP-1 (`gp-01-login-creator.png`)**: Authenticated as Creator Elena Chen; verified ModeChip displays `Mock` and Creator Dashboard displays demo checklist and active drafts.
  - **GP-2 (`gp-02-sample-review.png`)**: High-risk press release submission created; triggered mock review engine; 32 findings generated across Rule and AI categories; ModeChip verified `Mock`; Data Boundary panel verified 0 characters sent, 0 external calls, and explicit mock disclaimer.
  - **GP-3 (`gp-03-triage-actions.png`)**: Triaged findings: Accepted fix for "miracle" (created v2 in Draft, voided prior state), dismissed banned term "serum" with mandatory reason code `brand_exception` and justification, escalated clinical trial claim to brand manager; cleared remaining high-risk blockers.
  - **GP-4 (`gp-04-reviewer-changes-requested.png`)**: Creator submitted; Reviewer Marcus Vance claimed submission (`In Review`), posted threaded review comment on finding span, and submitted formal change request with note (`Changes Requested`).
  - **GP-5 (`gp-05-version-diff-and-approvals.png`)**: Creator revised content to v3 (`Draft`), re-checked in mock mode, resubmitted; Approver 1 (Reviewer Marcus Vance) approved (1 of 2 recorded, stayed `In Review`); Approver 2 (Brand Manager Jordan Reed) approved (2 of 2 recorded -> transitioned to `Approved`); computed clean version diff v1 -> v3 showing exact additions and removals.
  - **GP-6 (`gp-06-published-live.png`)**: Creator marked published with live URL (`https://brand.lumo.skincare/press/spring-hydration-v3`), transitioning status to `Marked Published`. Full cryptographic audit trail verified with 100 SHA-256 hash-chained entries.
- All SPEC section 12 negative and safety tests verified passing:
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
- Architecture contracts: `python manage.py arch` passed (Domain purity KEPT, Application isolation KEPT).
- Full test suite: `python manage.py test` passed 61/61 tests cleanly.

### Gate G3 Verification Notes (Production Run against PostgreSQL)
- Deployment Artifacts:
  - Multi-stage [Dockerfile](file:///home/redpanda/Documents/WeBug/Dockerfile) (Node 20 builder + Python 3.12 slim runner on `$PORT`).
  - Pre-built Next.js static export committed to `backend/app/static/` for low-memory Render native Python deployments.
  - Infrastructure-as-code [render.yaml](file:///home/redpanda/Documents/WeBug/render.yaml) specification with all environment variables.
  - Scheduled keep-alive GitHub Actions workflow ([keep_alive.yml](file:///home/redpanda/Documents/WeBug/.github/workflows/keep_alive.yml)) pinging `/api/v1/health` every 10 minutes.
  - Exhaustive click-by-click deployment manual ([docs/DEPLOYMENT.md](file:///home/redpanda/Documents/WeBug/docs/DEPLOYMENT.md)) with secret demarcation and pre-deployment safety checklist.
- Executed `scripts/verify_g3_production.py` on `http://localhost:8080` (FastAPI + PostgreSQL + Next.js static export):
  - **GP-1 (`g3-gp-01-login-roles.png`)**: Login and clearance tier verification passed for all 5 demo personas (Social Creator, Agency Creator, Reviewer, Brand Manager, Admin).
  - **GP-2 (`g3-gp-02-creator-review.png`)**: High-risk press release submitted, mock review triggered synchronously, 10 findings generated with exact cited knowledge base codes (`RULE-001`, `RULE-002`, `FACT-001`, etc.).
  - **GP-3 (`g3-gp-03-finding-actions.png`)**: Accepted fix created content Version 2 in `Draft`; dismissal without reason was refused with `HTTP 422`; dismissal with valid reason code (`brand_exception`) and justification transitioned finding to `dismissed`.
  - **GP-4 (`g3-gp-04-reviewer-approval.png`)**: Full revision and signoff cycle: Creator submitted -> Reviewer claimed -> Reviewer requested changes with note -> Creator updated content to Version 3 (`Draft`) -> Creator resubmitted -> Reviewer 1 approved (1 of 2 recorded) -> Brand Manager approved (2 of 2 recorded -> transitioned to `Approved`).
  - **GP-5 (`g3-gp-05-audit-export.png`)**: Brand Manager retrieved 65 hash-chained records and exported 66-line RFC-4180 CSV with SHA-256 block hashes.
  - **GP-6 (`g3-gp-06-admin-users.png`)**: Admin listed users, provisioned new creator user, and updated user role to reviewer.
  - **GP-7 (`g3-gp-07-mock-guardrails.png`)**: Confirmed `ai_mode=mock`; verified review completes with automatic fallback when `llm_daily_cap=0` and with zero outbound calls when `no_external_ai=True`.
  - **GP-8 (`g3-gp-08-insights-patterns.png`)**: Verified repeated-mistake patterns across 94 total reviews (80 synthetic history + live), 25 recurring issue clusters, 6 dismissal categories, and 44 rule counters.
- Additional Checks:
  - **Cold-Start UX**: 2000ms response detection and `<ColdStartBanner />` displaying *"Waking the server, this can take about a minute"*.
  - **Secret-Free Check**: 0 secrets found via `git grep` and `git log -p`.
  - **Component Gallery**: `/dev/ui/` reachable on local production server with HTTP 200 (`docs/evidence/g3-ui-gallery.png`).
- Full test suite: `python manage.py test` passed **64/64 tests**.
- Architecture contracts: `python manage.py arch` passed (**2 kept, 0 broken**).
